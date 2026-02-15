export const AVAILABLE_TAGS = [
  "converb",
  "yi+converb",
  "yi+present",
  "incompletive deverbal",
  "completive deverbal (past)",
  "completive deverbal (non-past)",
];

export const AVAILABLE_SUBCLAUSE_TYPES = [
  "advcl",
  "relcl",
  "ccomp",
  "xcomp",
  "acl",
  "csubj",
  "csubjpass",
];

export const SUBCLAUSE_TYPE_LABELS: Record<string, string> = {
  advcl: "Adverbial Clause Modifier",
  relcl: "Relative Clause Modifier",
  ccomp: "Clausal Complement",
  xcomp: "Open Clausal Complement",
  acl: "Adjectival Clause",
  csubj: "Clausal Subject",
  csubjpass: "Clausal Subject (Passive)",
};

export const TAG_LABELS: Record<string, string> = {
  converb: "Converb",
  "yi+converb": "Yi + Converb",
  "yi+present": "Yi + Present",
  "incompletive deverbal": "Incompletive Deverbal",
  "completive deverbal (past)": "Completive Deverbal (Past)",
  "completive deverbal (non-past)": "Completive Deverbal (Non-Past)",
};
