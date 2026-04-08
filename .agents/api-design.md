# API Design

## Error codes

Map exceptions to HTTP status codes consistently across all endpoints:

| Exception | Status | `detail` |
|-|-|-|
| `anthropic.AuthenticationError` | 500 | `"Service configuration error"` |
| `anthropic.APIStatusError` / `anthropic.APIConnectionError` | 502 | `"Upstream API error"` |
| `ValueError` (unexpected LLM response) | 500 | `"Unexpected response from LLM"` |
| MongoDB failure | 503 | `"Storage unavailable"` |
| Invalid ObjectId format | 400 | `"Invalid transcript ID format"` |
| Document not found | 404 | `"Transcript not found"` |

Claude and MongoDB errors in `POST /transcripts/search` both map to 503 — callers do not need to distinguish them.

## Pagination

All list endpoints must be paginated. Use `limit` and `skip` query parameters:

| Parameter | Default | Constraints |
|-|-|-|
| `limit` | 20 | 1–100 |
| `skip` | 0 | ≥ 0 |

Never use bare `find({})` with no `.limit()`.

## Claude API patterns

- Use `anthropic.AsyncAnthropic` (async client only)
- Instantiate with `@lru_cache` — never per request
- Use `tool_use` with `tool_choice={"type": "tool", "name": <tool_name>}` for structured output
- `tool_choice["name"]` must reference the tool definition's `"name"` field — no duplicate string literals
- Default to `max_retries=3` (SDK exponential backoff)

**Model selection:**

| Use case | Setting | Default |
|-|-|-|
| Transcript analysis | `CLAUDE_MODEL` | `claude-sonnet-4-6` |
| Topic/query mapping | `CLAUDE_SEARCH_MODEL` | `claude-haiku-4-5` |

## Pydantic constraints

Enforce constraints with `Field(...)` matching the corresponding JSON schema:

```python
qa_score: int = Field(..., ge=1, le=10)
topics: list[str] = Field(default_factory=list)
```

Array fields that default to empty must use `default_factory=list`, not `default=[]`.

## Named constants

No magic numbers for API parameters. Use named constants or `Settings` fields for `max_tokens`, `max_retries`, model identifiers, and tool names.

## `POST /analyze` save-before-return

`POST /transcripts/analyze` must persist the document before returning. A failed save must raise 503 — never silently return 200 with unsaved data.

## ObjectId validation

For `GET /{id}`, validate format before querying MongoDB:

```python
if not ObjectId.is_valid(id):
    raise HTTPException(status_code=400, detail="Invalid transcript ID format")
result = await repository.get_transcript_by_id(db, id)
if result is None:
    raise HTTPException(status_code=404, detail="Transcript not found")
```
