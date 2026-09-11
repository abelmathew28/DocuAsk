from __future__ import annotations

import re
from time import perf_counter
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.ai.citation_service import citation_excerpt, rank_citation_chunks, verify_answer
from app.ai.embeddings import EmbeddingService
from app.ai.factory import CompositeProvider, get_ai_provider
from app.ai.intent import Intent, classify_intent
from app.ai.list_answer import format_list_answer
from app.ai.local_provider import ExtractiveProvider, OllamaChatProvider, extract_from_passages
from app.ai.prompts import (
    build_context_block,
    build_user_prompt,
    insufficient_message,
    is_insufficient_answer,
    system_prompt,
)
from app.ai.provider import AIProvider
from app.ai.query_service import expand_search_query, rewrite_question
from app.ai.retrieval import MIN_RELEVANCE, RetrievalService
from app.ai.types import RetrievedChunk
from app.core.config import settings
from app.core.exceptions import AppError, ProviderError
from app.core.logging import get_logger
from app.models.conversation import SCOPE_LIBRARY, Conversation, Message, MessageRole, MessageSource
from app.models.document import Document, DocumentStatus
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.usage_repository import UsageRepository

logger = get_logger("ai.chat")

INSUFFICIENT_ANSWER = insufficient_message("document")


def title_from_question(question: str) -> str:
    cleaned = re.sub(r"\s+", " ", question).strip(" ?!.")
    cleaned = re.sub(
        r"^(what is|what's|whats|how many|how do|how should|how can|how does|when is|where is|who is|tell me about|explain)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = cleaned.strip(" ?!.") or question.strip()
    titled = cleaned[:48].title()
    return titled or "New conversation"


class ChatService:
    def __init__(self, db: Session, provider: Optional[AIProvider] = None) -> None:
        self.db = db
        self.conversations = ConversationRepository(db)
        self.documents = DocumentRepository(db)
        self.usage = UsageRepository(db)
        self.provider = provider
        self.retrieval = RetrievalService(db)

    def _provider(self) -> AIProvider:
        if self.provider is None:
            self.provider = get_ai_provider()
        return self.provider

    def retrieve(
        self,
        user_id: str,
        question: str,
        document_ids: Optional[List[str]],
        history: Optional[List[dict]] = None,
        intent: Optional[Intent] = None,
    ) -> List[RetrievedChunk]:
        provider = self._provider()
        embeddings = EmbeddingService(provider)
        rewritten = rewrite_question(question, history or [])
        search_query = expand_search_query(rewritten)
        listing = intent == Intent.LIST
        query_vector = embeddings.embed_query(search_query)
        chunks = self.retrieval.search(
            user_id=user_id,
            query_embedding=query_vector,
            document_ids=document_ids,
            query=search_query,
            top_k=16 if listing else settings.RERANK_TOP_K,
            candidates=40 if listing else settings.RETRIEVAL_CANDIDATES,
        )
        if chunks and all(0 <= chunk.score <= 1.5 for chunk in chunks[:3]):
            chunks = [chunk for chunk in chunks if chunk.score >= MIN_RELEVANCE]
        if listing:
            return self.retrieval.expand_same_pages(user_id, chunks, document_ids)
        return chunks[: settings.RERANK_TOP_K]

    def complete_from_chunks(
        self,
        question: str,
        chunks: List[RetrievedChunk],
        scope: str,
        history: Optional[List[dict]] = None,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        fallback = insufficient_message(scope)
        if not chunks:
            return fallback
        intent = classify_intent(question)
        if intent == Intent.LIST:
            answer = format_list_answer(question, chunks, fallback)
            if is_insufficient_answer(answer):
                return fallback
            verified, _ = verify_answer(answer, chunks, fallback)
            return verified

        def grounded() -> str:
            passages = [
                f"{chunk.heading}\n{chunk.text}" if chunk.heading and chunk.heading not in chunk.text else chunk.text
                for chunk in chunks
            ]
            return extract_from_passages(question, passages, fallback)

        context = build_context_block(
            [
                {
                    "document_name": chunk.document_name,
                    "page_number": chunk.page_number,
                    "text": chunk.text[:2000],
                    "heading": chunk.heading,
                }
                for chunk in chunks
            ]
        )
        provider = self._provider()
        llm = provider.llm if isinstance(provider, CompositeProvider) else provider
        if isinstance(llm, ExtractiveProvider):
            answer = grounded()
        else:
            user_prompt = build_user_prompt(question, context, fallback)
            llm_messages = (history or []) + [{"role": "user", "content": user_prompt}]
            try:
                answer = provider.complete(
                    system or system_prompt(scope),
                    llm_messages,
                    max_tokens=max_tokens or settings.OPENAI_MAX_OUTPUT_TOKENS,
                )
            except ProviderError as exc:
                logger.warning("llm_fallback_extractive", error=str(exc))
                answer = grounded()
            if is_insufficient_answer(answer):
                answer = grounded()
        if is_insufficient_answer(answer):
            return fallback
        verified, _ = verify_answer(answer, chunks, fallback)
        return verified

    def ask(
        self,
        conversation: Conversation,
        document: Optional[Document] = None,
        question: str = "",
        persist_user: bool = True,
        existing_user_message: Optional[Message] = None,
        mode: str = "ask",
    ) -> Tuple[Message, Message]:
        scope = conversation.scope or "document"
        fallback = insufficient_message(scope)
        ready_docs = self._ready_documents(conversation)
        if not ready_docs:
            raise AppError(
                "No ready documents in this search. Wait until indexing finishes, then try again.",
                status_code=409,
                code="not_ready",
            )

        started = perf_counter()
        history = self._history_messages(conversation)
        search_ids = None if scope == SCOPE_LIBRARY else [item.id for item in ready_docs]

        if mode == "research":
            from app.ai.research_service import ResearchService

            answer, used_chunks = ResearchService(self).run(conversation.user_id, question, search_ids, history)
        elif mode == "extract":
            from app.ai.extraction_service import ExtractionService

            answer, used_chunks = ExtractionService(self).run(conversation.user_id, question, search_ids, history)
        else:
            chunks = self.retrieve(conversation.user_id, question, search_ids, history, classify_intent(question, mode))
            answer = self.complete_from_chunks(question, chunks, scope, history)
            if is_insufficient_answer(answer):
                used_chunks = []
                answer = fallback
            else:
                answer, supported = verify_answer(answer, chunks, fallback)
                if answer == fallback:
                    used_chunks = []
                else:
                    used_chunks = rank_citation_chunks(answer, chunks) or supported

        latency = int((perf_counter() - started) * 1000)
        provider = self._provider()

        user_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER.value,
            content=question,
        ) if persist_user else None
        assistant_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT.value,
            content=answer,
            model=_llm_model_name(provider),
            latency_ms=latency,
            sources=[
                MessageSource(
                    document_chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    document_name=chunk.document_name,
                    page_number=chunk.page_number,
                    excerpt=citation_excerpt(answer, chunk),
                    relevance_score=round(chunk.score, 4),
                )
                for chunk in used_chunks[:6]
            ],
        )

        if conversation.title in {"New conversation", "New chat", "Library search", "Selected files"} and question:
            conversation.title = title_from_question(question)

        if user_message is not None:
            self.db.add(user_message)
        else:
            user_message = existing_user_message
        self.db.add(assistant_message)
        self.db.add(conversation)
        self.db.commit()
        if user_message is not None:
            self.db.refresh(user_message)
        self.db.refresh(assistant_message)
        self.usage.record(conversation.user_id, "ai_request", latency)
        self.usage.record(conversation.user_id, "question", latency)
        logger.info("chat_completed", conversation_id=conversation.id, latency_ms=latency, sources=len(used_chunks), mode=mode)
        return user_message, assistant_message

    def regenerate(self, conversation: Conversation, document: Optional[Document] = None) -> Optional[Tuple[Message, Message]]:
        messages = conversation.messages
        last_user = next((item for item in reversed(messages) if item.role == MessageRole.USER.value), None)
        last_assistant = next((item for item in reversed(messages) if item.role == MessageRole.ASSISTANT.value), None)
        if not last_user:
            raise AppError("There is no question to regenerate.", status_code=400, code="no_question")
        if last_assistant:
            self.db.delete(last_assistant)
            self.db.commit()
            self.db.refresh(conversation)
        return self.ask(
            conversation,
            conversation.document,
            last_user.content,
            persist_user=False,
            existing_user_message=last_user,
        )

    def _ready_documents(self, conversation: Conversation) -> List[Document]:
        scope = conversation.scope or "document"
        if scope == SCOPE_LIBRARY:
            return [
                item
                for item in self.documents.list_for_user(conversation.user_id, status=DocumentStatus.READY.value)
            ]
        wanted = conversation.parsed_document_ids()
        if not wanted and conversation.document:
            wanted = [conversation.document.id]
        ready: List[Document] = []
        for document_id in wanted:
            document = self.documents.get(document_id, conversation.user_id)
            if document and document.status == DocumentStatus.READY.value:
                ready.append(document)
        return ready

    def _history_messages(self, conversation: Conversation) -> List[dict]:
        recent = conversation.messages[-settings.CONVERSATION_HISTORY_MESSAGES :]
        payload = []
        for message in recent:
            content = message.content
            if message.role == "user" and len(content) > 500:
                content = content[:500]
            payload.append({"role": message.role, "content": content})
        return payload


def _llm_model_name(provider: AIProvider) -> str:
    llm = provider.llm if isinstance(provider, CompositeProvider) else provider
    if isinstance(llm, OllamaChatProvider):
        return settings.OLLAMA_MODEL
    if isinstance(llm, ExtractiveProvider):
        return "extractive"
    return settings.OPENAI_CHAT_MODEL
