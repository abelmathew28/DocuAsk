export function formatBytes(bytes: number): string {
  if (!bytes) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / Math.pow(1024, index)).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

export function formatDate(value: string): string {
  return new Date(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

export function relativeTime(value: string): string {
  const delta = Date.now() - new Date(value).getTime();
  const minutes = Math.round(delta / 60000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  if (days < 7) return `${days}d ago`;
  return formatDate(value);
}

export function apiError(error: unknown, fallback = 'Something went wrong.'): string {
  const detail = (error as { error?: { detail?: string } })?.error?.detail;
  return typeof detail === 'string' ? detail : fallback;
}

export function explainDocumentError(message: string | null | undefined): { title: string; body: string } | null {
  if (!message) return null;
  const lower = message.toLowerCase();
  if (lower.includes('api key') || lower.includes('openai')) {
    return {
      title: 'This file was saved, but it cannot be searched yet.',
      body: 'This file failed when indexing still required OpenAI. Indexing now runs locally — tap Retry. For stronger answers, add OPENAI_API_KEY or run Ollama (LLM_PROVIDER=ollama). Without those, Ask still works from the retrieved pages.',
    };
  }
  if (lower.includes('enough text') || lower.includes('extract')) {
    return {
      title: 'This PDF did not have enough readable text.',
      body: message,
    };
  }
  return {
    title: 'Indexing failed.',
    body: message,
  };
}
