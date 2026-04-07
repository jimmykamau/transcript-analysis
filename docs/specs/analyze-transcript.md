# Spec: POST /transcripts/analyze

## Overview

An endpoint that accepts a call center transcript and uses the Claude API to produce a structured QA analysis — score, justification, summary, and sentiment.

---

## Endpoint

```
POST /transcripts/analyze
Content-Type: application/json
```

---

## Request

### Body

| Field | Type | Constraints | Description |
|---|---|---|---|
| `transcript` | string | required, min length 1 | The full text of the call center transcript |

### Example

```json
{
  "transcript": "Agent: Thank you for calling TechSupport, my name is Carlos. How can I help you today?\nCustomer: Hi Carlos, I've been trying to reset my password for three days..."
}
```

---

## Response

### 200 OK

| Field | Type | Constraints | Description |
|---|---|---|---|
| `qa_score` | integer | 1–10 | Quality rating of the agent's interaction |
| `qa_justification` | string | one sentence | Explanation for the score |
| `summary` | string | 2–3 sentences | Summary of the conversation |
| `sentiment` | string | `positive` \| `neutral` \| `negative` | Overall customer sentiment |

### Example

```json
{
  "qa_score": 8,
  "qa_justification": "The agent resolved the customer's long-standing issue promptly and with empathy, though the repeated transfers prior to this call indicate a systemic gap.",
  "summary": "A frustrated customer who had been unable to reset their password for three days and had been transferred multiple times finally reached an agent who resolved the issue directly. The agent apologized for the prior experience, handled the reset personally, and confirmed the fix within minutes. The customer's tone shifted from frustration to satisfaction by the end of the call.",
  "sentiment": "positive"
}
```

---

## Error Responses

| Condition | Status | Detail |
|---|---|---|
| Missing or empty `transcript` | `422 Unprocessable Entity` | Pydantic validation error body |
| Missing/invalid `ANTHROPIC_API_KEY` or other config failure | `500 Internal Server Error` | `"Service configuration error"` |
| Invalid API key / auth failure (Anthropic rejects request) | `500 Internal Server Error` | `"Service configuration error"` |
| Claude API unreachable / rate-limited (after 3 retries) | `502 Bad Gateway` | `"Upstream API error"` |
| Unexpected LLM response structure | `500 Internal Server Error` | `"Unexpected response from LLM"` |

---

## Implementation Notes

### Claude API Integration

- Client: `anthropic.AsyncAnthropic` (async)
- Model: configurable via `CLAUDE_MODEL` env var, defaults to `claude-sonnet-4-6`
- Structured output via **tool_use** with `tool_choice={"type": "tool", "name": "analyze_transcript"}` — forces a JSON-schema-validated response rather than freeform text
- Retry: SDK-native `max_retries=3` with exponential backoff (no extra library needed)

### Tool Schema

The tool `analyze_transcript` has a JSON Schema `input_schema` that mirrors the response model:

```json
{
  "qa_score":       { "type": "integer", "minimum": 1, "maximum": 10 },
  "qa_justification": { "type": "string" },
  "summary":        { "type": "string" },
  "sentiment":      { "type": "string", "enum": ["positive", "neutral", "negative"] }
}
```

### System Prompt (summarized)

> You are a QA analyst evaluating customer service call transcripts. Call the `analyze_transcript` tool with a score (1–10), a one-sentence justification, a 2–3 sentence summary, and the customer's overall sentiment.

### Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | yes | — | Claude API key; app fails to start if absent |
| `CLAUDE_MODEL` | no | `claude-sonnet-4-6` | Model ID passed to the API |

---

## Domain Placement

This endpoint lives in the existing `app/transcripts/` domain:

```
app/transcripts/
├── router.py    ← adds POST /analyze
├── models.py    ← TranscriptRequest, TranscriptAnalysis
└── services.py  ← analyze_transcript() calling Claude
```

`app/main.py` already registers `app/transcripts/router.py` at the `/transcripts` prefix — no changes to `main.py` are required.

---

## Testing

Tests live in `tests/transcripts/test_analyze_transcript.py` and cover:

| Test | Input | Expected |
|---|---|---|
| Success | Valid transcript | 200 with correct JSON shape |
| Empty transcript | `{"transcript": ""}` | 422 |
| API failure | Mock raises `APIStatusError` | 502 |

The Claude API call is mocked via `unittest.mock.patch` on `app.transcripts.services.anthropic.AsyncAnthropic` — no real API calls are made in tests.

---

## Review Items

| # | Area | Issue | Status |
|-|-|-|-|
| 1 | services.py | `max_tokens=1024` is hardcoded — consider exposing as `CLAUDE_MAX_TOKENS` in `Settings` if callers need control over response length | closed |
| 2 | services.py / models.py | `_TOOL["input_schema"]` is hand-coded and duplicates the shape of `TranscriptAnalysis`. Could be generated via `TranscriptAnalysis.model_json_schema()` to keep a single source of truth | closed |
