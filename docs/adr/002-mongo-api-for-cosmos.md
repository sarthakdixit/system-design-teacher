# ADR-002: MongoDB API on Cosmos DB (not native Cosmos SDK)

- **Status:** Accepted
- **Date:** 2026-04-30
- **Deciders:** Project owner
- **Related:** ADR-001 (ports & adapters), DESIGN.md §4.3, §12.1, Batch 5 plan

---

## Context

The platform needs a NoSQL document database for users, questions, attempts, rate-limit counters, and feedback cache. Local development uses MongoDB 7 in Docker. Production will use Azure Cosmos DB (chosen for its free tier and managed-service simplicity).

Cosmos DB exposes multiple **APIs** on top of the same underlying engine:

1. **MongoDB API** — wire-compatible with MongoDB 4.x/5.x. Drivers like `pymongo` and `motor` connect with a connection string and "just work."
2. **NoSQL API** (formerly "Core API") — native Cosmos protocol. Different SDK (`azure-cosmos`), different request shape, different query language (SQL-like rather than MongoDB query operators).
3. **Cassandra API**, **Gremlin API**, **Table API** — not relevant.

We must pick one. The choice has cascading implications: the database adapter, the local-vs-cloud parity story, and the migration effort if we ever want to switch.

---

## Decision

Use the **MongoDB API**. Local development uses real MongoDB 7. Azure deployment uses Cosmos DB configured to expose the MongoDB API. Both are accessed via the `motor` async driver with a connection-string-only configuration difference.

### What this means concretely

- The `MongoDBDatabase` adapter (Batch 1) works against both local Mongo and Cosmos with **zero code changes**. Only the `MONGO_URI` environment variable changes.
- In Batch 5, we don't even need a separate `CosmosDatabase` adapter. The `MongoDBDatabase` adapter IS the Cosmos adapter. The DI container's `Selector` is essentially a no-op for the Database port — both branches resolve to the same class with different config.
- The `Database` Protocol (port) stays focused on MongoDB-style operations: `find_one`, `find_one_and_update`, aggregation pipelines, TTL indexes. No Cosmos-specific concepts leak into the port.

---

## Consequences

### Positive

- **Local-prod parity is real.** Code that works against `mongodb://localhost:27018` works against `mongodb://your-cosmos.mongo.cosmos.azure.com:10255` with no changes. The same query, the same operators, the same index types.
- **No second SDK to learn or maintain.** `motor` is well-documented, mature, and async-native. The Cosmos NoSQL SDK is also good, but learning it AND `motor` doubles the cognitive load.
- **Standard query language.** MongoDB query operators (`$match`, `$sample`, `$inc`) are widely known. Cosmos NoSQL's SQL-like syntax is non-standard — neither SQL nor MongoDB-y, just its own thing.
- **Trivial migration path off Azure.** If we ever leave Azure for any reason, the same Mongo driver works against MongoDB Atlas, AWS DocumentDB, or self-hosted Mongo. Cosmos NoSQL API would lock us in.
- **No code changes for Batch 5.** The biggest near-term win. We swap a connection string in Key Vault and the app moves to Cosmos.

### Negative

- **Cosmos's MongoDB API trails real MongoDB by ~1–2 versions.** New MongoDB features take time to land in Cosmos. We've checked: nothing we use (TTL indexes, `$sample`, `findOneAndUpdate` with upsert) is recent enough to be unsupported. Future-proofing concern, not current-blocker.
- **Some MongoDB operators are unsupported.** Cosmos's compat surface is wide but not 100%. Edge cases (some `$expr` patterns, certain aggregation stages) may behave differently. Mitigation: integration tests against both backends in CI, planned for Batch 6.
- **Cosmos's RU-based pricing model still applies.** The MongoDB-compatible API is just a wire protocol layer. Underneath, you still pay for Request Units. This is independent of the API choice; it's how Cosmos bills.
- **Slightly less control over indexing strategies.** Cosmos has its own opinions about automatic indexing. We've reviewed: our compound indexes (questions, attempts) and TTL indexes (rate-limit counters, feedback cache) all work the same way. No issues for our access patterns.

### Neutral

- **Connection strings differ.** Local Mongo uses `mongodb://...:27017`. Cosmos Mongo API uses `mongodb://...:10255?ssl=true&...`. Both go in env vars; neither is exposed in code.
- **TTL indexes work identically.** Cosmos honors MongoDB-style TTL indexes for the feedback cache cleanup.

---

## Alternatives considered

### 1. Cosmos NoSQL API with the native SDK

- ✅ Slightly cheaper RU consumption for some access patterns.
- ✅ More features land here first.
- ❌ Different SDK from local development. Means writing a `CosmosDatabase` adapter that doesn't share code with `MongoDBDatabase`.
- ❌ Different query language. Two mental models to maintain.
- ❌ Lock-in. Migrating off Azure later requires rewriting the data layer.
- **Rejected** — the parity loss is the big cost, and the wins are marginal at our scale.

### 2. PostgreSQL (Azure Database for PostgreSQL)

- ✅ Mature, well-known relational store.
- ✅ Strong consistency, foreign keys, etc.
- ❌ Document data (diagram JSON, structured feedback) doesn't map naturally to tables. Would force JSON columns or contortions.
- ❌ TTL on rate-limit counters and feedback cache requires either a separate cleanup job or a `pg_cron` extension. We get this free with Mongo TTL indexes.
- ❌ Different paradigm than the local dev story (which is already Mongo).
- **Rejected** — wrong shape for this data, and switching would mean rebuilding Batches 1–3.

### 3. Self-hosted MongoDB on Azure (VM or AKS)

- ✅ Full MongoDB compatibility, no API gaps.
- ❌ We operate the database. Backups, upgrades, scaling, security patches.
- ❌ No free tier. VM costs money even when idle.
- ❌ Defeats the "operate on free tiers" goal.
- **Rejected** — operational overhead is too high for a portfolio project.

### 4. Azure SQL Database

- ✅ Cheap, managed, well-known.
- ❌ Same shape mismatch as PostgreSQL.
- **Rejected** — same reasons.

### 5. Cosmos DB with Mongo API for documents + Redis on Azure for cache/rate-limiting

- ✅ Specialized stores for specialized needs.
- ❌ Adds a service to provision, monitor, and pay for. Cosmos DB free tier alone gives us 1000 RU/s; we don't need Redis on top.
- ❌ More complex DI wiring.
- **Deferred** — we keep it as a contingency if Mongo TTL/counter performance becomes a bottleneck. So far there's no evidence it will.

---

## Open questions

- **At what scale does the MongoDB-API performance gap (vs native Cosmos) bite?** Probably above 100 RU/s sustained. We're at <10 RU/s in MVP. Worth measuring before any production launch.
- **Does Cosmos free tier support TTL indexes?** Confirmed: yes, but TTL granularity is at the document level, polled every ~minute. Acceptable for our cache and rate-limit cleanup.
- **Will we ever want change feeds / event-driven processing?** Cosmos NoSQL API has change feed natively. The MongoDB API exposes change streams instead. Both work. Out of scope for MVP.

---

## References

- [Azure Cosmos DB for MongoDB documentation](https://learn.microsoft.com/azure/cosmos-db/mongodb/)
- [Cosmos DB MongoDB API supported features](https://learn.microsoft.com/azure/cosmos-db/mongodb/feature-support-50)
- ADR-001 (this repo) — ports & adapters
- DESIGN.md §4.3 (this repo) — tech stack
