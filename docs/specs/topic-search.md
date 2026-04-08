# Spec: Topic Search for Transcripts

## Overview

Transcripts are tagged with topic slugs at ingestion time (e.g. `"apology"`, `"pricing"`, `"escalation"`). Clients can then filter the transcript list by topic or submit a free-form natural-language query that Claude maps to matching slugs.

---

## Updated Endpoint: POST /transcripts/analyze

Response gains one new field:

| Field | Type | Description |
|---|---|---|
| `topics` | array of strings | Short lowercase slugs identifying key themes in the call |

### Example response (addition only)

```json
{
  "topics": ["apology", "password_reset"]
}
```

---

## Updated Endpoint: GET /transcripts/

Gains an optional `topic` filter parameter. Response items also gain `summary` and `topics` fields (these apply to all `GET /transcripts/` responses, not only filtered ones).

**Query parameters (additions):**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `topic` | string | `null` | When set, returns only transcripts tagged with this slug |

**Response items gain:**

| Field | Type | Description |
|---|---|---|
| `summary` | string | 2–3 sentence overview of the call |
| `topics` | array of strings | Topic slugs attached to this transcript |

### Example

```
GET /transcripts/?topic=apology
```

```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "qa_score": 7,
    "sentiment": "negative",
    "summary": "Customer called to dispute a charge. Agent apologized for the error and issued a refund.",
    "created_at": "2024-01-15T10:30:00Z",
    "topics": ["apology", "escalation"]
  }
]
```

---

## New Endpoint: GET /transcripts/topics

Returns the distinct list of topic slugs present across all stored transcripts.

**Response — 200 OK** — `application/json` array of strings:

```json
["apology", "billing", "escalation", "password_reset", "pricing", "technical_issue"]
```

---

## New Endpoint: POST /transcripts/search

Accepts a free-form natural-language query. Claude maps it to matching topic slugs (chosen from those that actually exist in the database), then returns matching transcripts.

### Request body

| Field | Type | Constraints | Description |
|---|---|---|---|
| `query` | string | required, min length 1 | Natural-language description of calls to find |

### Example

```json
{ "query": "calls where the agent apologized" }
```

### Response — 200 OK

Same shape as `GET /transcripts/` items (array of `TranscriptSummary` with `topics`).

```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "qa_score": 7,
    "sentiment": "negative",
    "summary": "Customer called to dispute a charge. Agent apologized for the error and issued a refund.",
    "created_at": "2024-01-15T10:30:00Z",
    "topics": ["apology", "escalation"]
  }
]
```

If Claude cannot map the query to any known topic, returns an empty array `[]` with status 200.

### Internal flow

```
POST /transcripts/search { "query": "..." }
  │
  ├─ repository.list_topics(db)
  │    └─ distinct("topics") from MongoDB
  │
  ├─ services.interpret_query(query, available_topics, settings)
  │    └─ Claude: maps query → ["apology"] (only picks from available_topics)
  │
  └─ repository.search_by_topics(db, ["apology"], skip, limit)
       └─ { topics: { $in: ["apology"] } }
```

---

## Error Responses

| Endpoint | Condition | Status | Detail |
|---|---|---|---|
| `POST /transcripts/search` | Empty `query` | `422 Unprocessable Entity` | FastAPI validation error |
| `POST /transcripts/search` | MongoDB or Claude failure | `503 Service Unavailable` | `"Storage unavailable"` |
| `GET /transcripts/topics` | MongoDB failure | `503 Service Unavailable` | `"Storage unavailable"` |
| `GET /transcripts/` | MongoDB failure (unchanged) | `503 Service Unavailable` | `"Storage unavailable"` |

---

## MongoDB Document Schema (additions)

| Field | BSON type | Description |
|---|---|---|
| `topics` | array of strings | Topic slugs; absent on documents ingested before this feature |

### Index

```
db.transcripts.createIndex({ topics: 1 })
```

MongoDB indexes array fields natively — each element becomes an index entry, so `{ topics: "apology" }` and `{ topics: { $in: [...] } }` both use the index.

---

## Topic Slug Format

Slugs are short, lowercase, underscore-separated strings. Claude is instructed to pick from a fixed vocabulary that includes (but is not limited to):

`apology`, `billing`, `cancellation`, `escalation`, `password_reset`, `pricing`, `refund`, `technical_issue`, `wait_time`

New slugs may appear organically as Claude describes novel call themes.

---

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `CLAUDE_SEARCH_MODEL` | no | `claude-haiku-4-5` | Model used for `interpret_query` (the slug-mapping call). Separate from `CLAUDE_MODEL` so a cheaper/faster model can be used for search without affecting analysis quality. |

`ANTHROPIC_API_KEY`, `CLAUDE_MODEL`, and `CLAUDE_MAX_TOKENS` are unchanged.

---

## Domain Placement

```
app/transcripts/
├── router.py      ← GET /topics, POST /search; topic param on GET /
├── schemas.py     ← topics field on TranscriptAnalysis, TranscriptSummary;
│                     new TranscriptSearchRequest
├── models.py      ← topics field on TranscriptDocument
├── repository.py  ← list_topics(), search_by_topics(); topic filter on list_transcripts()
└── services.py    ← topics in _SYSTEM prompt; new interpret_query()
```

`app/main.py` lifespan creates the `topics` index after connecting.

---

## Testing

| Test | Endpoint/Unit | Setup | Expected |
|---|---|---|---|
| Analyze response includes topics | `POST /analyze` | Mock block.input includes `topics` | 200 with `topics` array |
| Topic filter forwarded | `GET /?topic=apology` | Mock `repository.list_transcripts` | called with `topic="apology"` |
| No topic filter | `GET /` | Mock `repository.list_transcripts` | called with `topic=None` |
| List topics | `GET /topics` | Mock `repository.list_topics` | 200 slug array |
| Search success | `POST /search` | Mock `list_topics`, `interpret_query` → `["apology"]`, `search_by_topics` | 200 with matching summaries |
| Search no match | `POST /search` | `interpret_query` returns `[]` | 200 empty array |
| Search empty query | `POST /search` | No mock | 422 |
