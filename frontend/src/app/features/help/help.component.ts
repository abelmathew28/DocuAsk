import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-help',
  imports: [RouterLink],
  template: `
    <article class="mx-auto max-w-2xl">
      <h1 class="font-display text-4xl tracking-tight">Guide</h1>
      <ol class="mt-8 space-y-5 text-[15px] leading-7 text-ink-700">
        <li><strong>1. Upload a file.</strong> PDF, Word, or text. Wait until status is Ready. If it fails, read the note on the file, then tap Retry.</li>
        <li><strong>2. Choose the search.</strong> One file, a few files, or the whole library. Use Ask, Research, Compare, or Extract.</li>
        <li><strong>3. Read the citation.</strong> Every answer should show the document name and page. Click it to jump there and highlight the passage. If there is no citation, the answer was not in the file.</li>
        <li><strong>4. Keep the thread.</strong> Rename it, copy it, export it as Markdown, or delete it from the header.</li>
      </ol>
      <p class="mt-10 text-sm leading-6 text-ink-600">
        Indexing does not need OpenAI. Answers use OpenAI when a key is set, Ollama when <span class="font-medium">LLM_PROVIDER=ollama</span>, or the retrieved pages if neither is available.
      </p>
      <h2 class="mt-12 text-sm font-medium">Keyboard</h2>
      <dl class="mt-3 space-y-2 text-sm">
        <div class="flex justify-between border-b border-paper-200 py-2 dark:border-white/10"><dt>Search files</dt><dd class="text-ink-600">⌘K</dd></div>
        <div class="flex justify-between border-b border-paper-200 py-2 dark:border-white/10"><dt>Shortcuts</dt><dd class="text-ink-600">?</dd></div>
        <div class="flex justify-between border-b border-paper-200 py-2 dark:border-white/10"><dt>Focus the question box</dt><dd class="text-ink-600">/</dd></div>
        <div class="flex justify-between py-2"><dt>Send</dt><dd class="text-ink-600">Enter</dd></div>
      </dl>
      <a routerLink="/app" class="btn-ink mt-10">Open files</a>
    </article>
  `,
})
export class HelpComponent {}
