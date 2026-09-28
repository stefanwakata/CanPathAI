export type Lang = "fr" | "en";

export interface UserProfile {
  noc_code?: string;
  occupation?: string;
  province?: string;
  country_of_citizenship?: string;
  status?: string;
  years_experience?: number;
  language?: Lang;
}

export interface Citation {
  label: string;
  source: string;
  url?: string | null;
}

export interface Visualization {
  title: string;
  figure: { data: unknown[]; layout: Record<string, unknown> };
}

export interface ChatResponse {
  session_id: string;
  answer: string;
  language: string;
  citations: Citation[];
  visualizations: Visualization[];
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  visualizations?: Visualization[];
  error?: boolean;
}

export interface RagasMetric {
  name: string;
  value: number;
}

export interface IngestionRun {
  dataset: string;
  status: string;
  rows_loaded: number;
  started_at: string;
}

export interface StatsResponse {
  ragas: RagasMetric[];
  evaluated_at?: string | null;
  n_questions: number;
  ingestion: IngestionRun[];
}
