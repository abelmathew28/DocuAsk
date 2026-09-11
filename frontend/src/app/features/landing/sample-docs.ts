export type SampleDemoKey = 'withdraw' | 'refund' | 'integrity';

export interface SampleDemo {
  key: SampleDemoKey;
  short: string;
  file: string;
  page: number;
  section: string;
  question: string;
  answer: string;
  citation: string;
  excerpt: string;
  supportStatus: 'supported' | 'partially_supported' | 'not_found';
  highlightIds: number[];
}

export const SAMPLE_DEMOS: SampleDemo[] = [
  {
    key: 'withdraw',
    short: 'Withdraw',
    file: 'Fall-2026-Academic-Calendar.pdf',
    page: 2,
    section: 'Withdrawal Deadlines',
    question: 'What is the last day to withdraw from a Fall 2026 course?',
    answer:
      'The last day to withdraw from a Fall 2026 course without academic penalty is Friday, November 6, 2026.',
    citation: 'Fall-2026-Academic-Calendar.pdf — Page 2',
    excerpt: 'Last day to withdraw from a Fall 2026 course: Friday, November 6, 2026.',
    supportStatus: 'supported',
    highlightIds: [0, 1, 2, 8],
  },
  {
    key: 'refund',
    short: 'Refund',
    file: 'Fall-2026-Academic-Calendar.pdf',
    page: 3,
    section: 'Tuition Refund Schedule',
    question: 'What is the tuition refund deadline for Fall 2026?',
    answer:
      'A 100% tuition refund is available through the end of the first week of classes (September 4, 2026). After that date, refunds follow the published schedule.',
    citation: 'Fall-2026-Academic-Calendar.pdf — Page 3',
    excerpt: '100% refund through Friday, September 4, 2026 (end of week one).',
    supportStatus: 'supported',
    highlightIds: [3, 4, 5, 12],
  },
  {
    key: 'integrity',
    short: 'Integrity',
    file: 'Student-Handbook-Excerpt.pdf',
    page: 1,
    section: 'Academic Integrity',
    question: 'What happens if a student is found responsible for plagiarism?',
    answer:
      'A first finding of plagiarism may result in a failing grade on the assignment and a written warning. Repeated violations may lead to course failure or suspension, as described in the student handbook.',
    citation: 'Student-Handbook-Excerpt.pdf — Page 1',
    excerpt: 'First offense: failing grade on the assignment and a written warning to the student.',
    supportStatus: 'supported',
    highlightIds: [6, 7, 9, 14],
  },
];

export const WORKFLOW_STEPS = [
  { title: 'Upload', body: 'PDF, Word, or text — validated and stored on your account.' },
  { title: 'Extract', body: 'Pages become searchable text with structure preserved.' },
  { title: 'Search', body: 'Hybrid keyword and vector retrieval find matching passages.' },
  { title: 'Answer', body: 'The model replies only from retrieved context.' },
  { title: 'Verify', body: 'Open the cited page and read the highlighted excerpt.' },
];

export const PRODUCT_FEATURES = [
  {
    title: 'Ask',
    body: 'Concise answers from selected documents with page-level citations.',
  },
  {
    title: 'Research',
    body: 'Cross-document synthesis with multiple sources and conflicting-evidence notes.',
  },
  {
    title: 'Compare',
    body: 'Compare two documents or versions and surface additions, removals, and changed language.',
  },
  {
    title: 'Extract',
    body: 'Pull structured fields into tables you can copy or export as CSV.',
  },
];

export const ARCHITECTURE_NODES = [
  'Angular',
  'FastAPI',
  'Document Processing',
  'Hybrid Retrieval',
  'Reranking',
  'Answer Generation',
  'Citation Verification',
];

/** Offline demo responses when the API is unavailable (clearly labeled demo samples). */
export const OFFLINE_DEMO_QA = SAMPLE_DEMOS.map((item) => ({
  question: item.question,
  answer: item.answer,
  citation: item.citation,
  excerpt: item.excerpt,
  file: item.file,
  page: item.page,
  supportStatus: item.supportStatus,
  label: 'Demo sample',
}));
