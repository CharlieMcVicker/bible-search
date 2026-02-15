export interface Tag {
  word_index: number;
  tag: string;
}

export interface SearchResult {
  ref_id: string;
  syllabary: string;
  phonetic: string;
  english: string;
  audio?: string;
  tags?: Tag[];
}

export interface Filters {
  use_lemma: boolean;
  is_hypothetical: boolean;
  is_command: boolean;
  is_time_clause: boolean;
  subclause_types: string[];
  tag: string;
}

export interface ActiveWord {
  word: string;
  sentenceId: string;
  wordIndex: number;
}
