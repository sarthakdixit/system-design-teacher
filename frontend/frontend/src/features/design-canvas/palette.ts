import type { ComponentType } from "./types";

export type PaletteItem = {
  type: ComponentType;
  label: string;
  defaultLabel: string;
  icon: string;
  category: "edge" | "service" | "data" | "infra";
  description: string;
};

export const PALETTE: PaletteItem[] = [
  {
    type: "user",
    label: "User",
    defaultLabel: "User",
    icon: "👤",
    category: "edge",
    description: "End user or client device hitting the system.",
  },
  {
    type: "cdn",
    label: "CDN",
    defaultLabel: "CDN",
    icon: "🌐",
    category: "edge",
    description: "Content delivery network for static assets and edge caching.",
  },
  {
    type: "load_balancer",
    label: "Load Balancer",
    defaultLabel: "Load Balancer",
    icon: "⚖️",
    category: "edge",
    description: "Distributes incoming traffic across backend instances.",
  },
  {
    type: "api_gateway",
    label: "API Gateway",
    defaultLabel: "API Gateway",
    icon: "🚪",
    category: "edge",
    description: "Routes API requests, handles auth, rate limiting, request transformation.",
  },
  {
    type: "rate_limiter",
    label: "Rate Limiter",
    defaultLabel: "Rate Limiter",
    icon: "🚦",
    category: "edge",
    description: "Per-user or per-key request rate enforcement.",
  },
  {
    type: "auth_service",
    label: "Auth Service",
    defaultLabel: "Auth Service",
    icon: "🔐",
    category: "service",
    description: "Authentication and session management.",
  },
  {
    type: "microservice",
    label: "Microservice",
    defaultLabel: "Service",
    icon: "⚙️",
    category: "service",
    description: "Backend service implementing business logic.",
  },
  {
    type: "notification_service",
    label: "Notification Service",
    defaultLabel: "Notification Service",
    icon: "🔔",
    category: "service",
    description: "Push, email, or SMS dispatch.",
  },
  {
    type: "cache",
    label: "Cache",
    defaultLabel: "Cache",
    icon: "⚡",
    category: "data",
    description: "In-memory cache (e.g., Redis) for hot reads.",
  },
  {
    type: "database",
    label: "Database",
    defaultLabel: "Database",
    icon: "🗄️",
    category: "data",
    description: "Persistent storage — relational or NoSQL.",
  },
  {
    type: "object_storage",
    label: "Object Storage",
    defaultLabel: "Object Storage",
    icon: "📦",
    category: "data",
    description: "Blob storage (e.g., S3) for files, images, large objects.",
  },
  {
    type: "search_index",
    label: "Search Index",
    defaultLabel: "Search Index",
    icon: "🔍",
    category: "data",
    description: "Full-text search (e.g., Elasticsearch, OpenSearch).",
  },
  {
    type: "queue",
    label: "Queue",
    defaultLabel: "Queue",
    icon: "📬",
    category: "infra",
    description: "Async messaging — Kafka, SQS, RabbitMQ.",
  },
  {
    type: "analytics",
    label: "Analytics",
    defaultLabel: "Analytics",
    icon: "📊",
    category: "infra",
    description: "Event ingestion and aggregation for dashboards.",
  },
];

export const PALETTE_BY_TYPE: Record<ComponentType, PaletteItem> = PALETTE.reduce(
  (acc, item) => {
    acc[item.type] = item;
    return acc;
  },
  {} as Record<ComponentType, PaletteItem>,
);

export const PALETTE_CATEGORIES: { id: PaletteItem["category"]; label: string }[] = [
  { id: "edge", label: "Edge" },
  { id: "service", label: "Services" },
  { id: "data", label: "Data" },
  { id: "infra", label: "Infrastructure" },
];
