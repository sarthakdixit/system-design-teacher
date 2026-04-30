export const CATEGORIES = [
  { value: "caching", label: "Caching" },
  { value: "scalability", label: "Scalability" },
  { value: "databases", label: "Databases" },
  { value: "security", label: "Security" },
  { value: "messaging", label: "Messaging" },
  { value: "reliability", label: "Reliability" },
  { value: "observability", label: "Observability" },
  { value: "networking", label: "Networking" },
  { value: "data-modeling", label: "Data Modeling" },
  { value: "system-tradeoffs", label: "System Tradeoffs" },
] as const;

export const DIFFICULTIES = [
  { value: "junior", label: "Junior" },
  { value: "mid", label: "Mid" },
  { value: "senior", label: "Senior" },
] as const;

export type CategoryValue = (typeof CATEGORIES)[number]["value"];
export type DifficultyValue = (typeof DIFFICULTIES)[number]["value"];
