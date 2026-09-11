import { DocumentItem } from '../core/models/models';

type Intelligence = {
  sections?: string[];
  topics?: string[];
};

export function documentBrief(doc: DocumentItem | undefined): string {
  if (!doc) return '';
  const sections = usefulSections(doc);
  if (sections.length) return sections.slice(0, 8).join(' · ');
  if (doc.summary && !isContactDump(doc.summary)) return doc.summary;
  if (doc.page_count) return `${doc.page_count} page${doc.page_count === 1 ? '' : 's'}`;
  return '';
}

export function starterQuestions(doc: DocumentItem | undefined): string[] {
  if (!doc) return [];
  const hay = haystack(doc);
  const sections = usefulSections(doc);
  const out: string[] = [];

  if (looksLikeResume(hay, sections)) {
    const catalog: Array<[string, string]> = [
      ['experience', 'What experience is listed?'],
      ['skill', 'What skills are listed?'],
      ['educat', 'What education is listed?'],
      ['project', 'What projects are described?'],
      ['intern', 'What internships or roles are mentioned?'],
      ['certif', 'What certifications are listed?'],
    ];
    for (const [needle, question] of catalog) {
      if (hay.includes(needle)) out.push(question);
    }
    if (!out.length) {
      return [
        'What experience is listed?',
        'What skills are listed?',
        'What education is listed?',
      ];
    }
    return unique(out, 6);
  }

  for (const section of sections.slice(0, 6)) {
    out.push(`What does this document say about ${section}?`);
  }

  for (const question of doc.suggested_questions || []) {
    if (isGenericFiller(question)) continue;
    if (isHandbookOnly(question) && !looksLikeHandbook(hay)) continue;
    out.push(question);
  }
  return unique(out, 6);
}

function usefulSections(doc: DocumentItem): string[] {
  const intel = (doc.intelligence || {}) as Intelligence;
  const raw = [...(intel.sections || []), ...(intel.topics || [])];
  return unique(
    raw.filter((item) => item && !isNameOrContact(item)),
    12,
  );
}

function haystack(doc: DocumentItem): string {
  const intel = (doc.intelligence || {}) as Intelligence;
  return [
    doc.name,
    doc.original_filename,
    doc.summary || '',
    ...(intel.sections || []),
    ...(intel.topics || []),
    ...(doc.suggested_questions || []),
  ]
    .join(' ')
    .toLowerCase();
}

function looksLikeResume(hay: string, sections: string[]): boolean {
  const heading = sections.join(' ').toLowerCase();
  return (
    /linkedin|github\.com|resume|curriculum/.test(hay) ||
    /experience|education|skills/.test(heading) ||
    (hay.includes('@') && /\d{3}/.test(hay) && /experience|skill|educat/.test(hay))
  );
}

function looksLikeHandbook(hay: string): boolean {
  return /vacation|handbook|policy|sick leave|remote work|benefit/.test(hay);
}

function isGenericFiller(question: string): boolean {
  return /most important rules|numbers, dates, or limits|should someone do first|who should be contacted|answers come from the indexed/i.test(
    question,
  );
}

function isHandbookOnly(question: string): boolean {
  return /vacation policy|sick days|remote work|report an absence|working hours|confidentiality policy/i.test(question);
}

function isContactDump(text: string): boolean {
  if (!text) return true;
  const hasEmail = /@/.test(text);
  const hasPhone = /\d{3}[-.\s)]\s*\d{3}/.test(text);
  return hasEmail || (hasPhone && text.length < 220) || /linkedin\./i.test(text);
}

function isNameOrContact(text: string): boolean {
  const value = text.trim();
  if (!value || isContactDump(value)) return true;
  if (/^[A-Z][A-Z\s.'-]{4,60}$/.test(value) && value.split(/\s+/).length <= 5) return true;
  return false;
}

function unique(values: string[], limit: number): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const value of values) {
    const key = value.replace(/\s+/g, ' ').trim();
    if (!key || seen.has(key.toLowerCase())) continue;
    seen.add(key.toLowerCase());
    out.push(key);
    if (out.length >= limit) break;
  }
  return out;
}
