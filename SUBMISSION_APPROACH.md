# Approach Document (for SHL Assessment Recommender)

Version: 1.0 | Last updated: 11 May 2026

## 1) Design choices

### Goal
Build a conversational agent that turns a vague hiring need into a grounded shortlist of **SHL Individual Test Solutions** using only catalog evidence.

### Key constraints we designed for
- **FastAPI** service with **GET `/health`** and **POST `/chat`**.
- **Stateless API**: every request carries the full conversation history; no server-side per-user state.
- **Schema compliance**: response must always match the required JSON schema.
- **Catalog-only outputs**: recommendations include **only SHL catalog URLs**.
- **Turn limits**: evaluator caps each conversation at 8 turns.
- **Refinement & comparison**: support mid-conversation edits and “difference between X and Y”.

### Stack
- **FastAPI** (HTTP API, schema via Pydantic)
- **Local catalog ingestion** from `shl_product_catalog.json`
- **Rule-based conversational logic** (deterministic parsing + scoring)

> Note: This implementation does not call an external LLM. Instead, it extracts constraints via keyword/regex and ranks catalog entries deterministically, ensuring groundedness (no hallucinated tests).

## 2) Retrieval setup (catalog ingestion)

The SHL catalog JSON file can contain problematic characters. To make ingestion robust, the project uses a **three-tier loading strategy** in `catalog.py`:

1. **Standard JSON load**
   - Reads the file as text
   - Removes control characters using regex
   - Parses JSON
2. **Fallback line-by-line/brace-depth extraction**
   - Repairs/cleans control characters
   - Extracts individual JSON objects by scanning braces `{...}`
   - Attempts JSON parsing on each extracted object

After loading, the catalog manager indexes items in memory:
- `items`: list of all catalog entities
- `items_by_name`, `items_by_id` (optional convenience)

This “retrieval” layer is therefore **catalog evidence lookup + lightweight keyword matching**, not embedding/vector search.

## 3) Prompt / agent design

### Where conversation logic lives
- `agent.py`: `AssessmentRecommender.process_message()`
- It reconstructs context from the **incoming message + full history** (stateless design).

### Context extraction (constraints)
We parse constraints using keyword maps + regex:
- **Job level**: entry / mid / senior / manager / director / executive
- **Purpose**: selection / development / benchmarking
- **Assessment category/type hints**: e.g. personality, knowledge, ability, situational, motivation, competencies, development
- **Years of experience**: regex for `N years|yrs`

### Behavior routing
For each user turn, the agent decides:
1. **Refusal** (off-topic / legal / general hiring advice / prompt injection style requests)
2. **Comparison** when the message contains comparison cues like “difference”, “compare”, “vs”
3. **Clarification** when context is insufficient
4. **Recommendation** when at least some constraints are present

### Recommendation ranking
`_generate_recommendations()` scores each catalog item using a weighted sum:
- Job-level match
- Assessment type/key match
- Keyword hits in name/description

Then it returns top **up to 10** items. Recommendations contain:
- `name`
- `url` (must come from the catalog)
- `test_type` (single-letter code derived from the catalog `keys`)

## 4) Evaluation method

This repository includes integration tests that validate core requirements:
- `GET /health` returns ok
- `POST /chat` responds with correct schema fields
- Vague queries return **empty recommendations**
- Off-topic requests trigger **refusal** with **empty recommendations**
- Multi-turn behavior can progress through clarification and recommendation

Files:
- `integration_test.py`
- `test_system.py`

### What we measure (locally)
- Deterministic behavior across sample conversations
- Recommendation presence after enough context
- Refusal correctness

> The official evaluator will additionally score Recall@10 and groundedness. This implementation is designed to maximize groundedness by restricting output to catalog evidence.

## 5) What did not work (and mitigations)

### Catalog parsing instability
Initial catalog loading attempts failed due to invalid control characters. Mitigation:
- Added cleanup of control characters before parsing.
- Added an aggressive brace-depth object extraction fallback.

### Over-eager recommendations
If recommendations are returned too early, it harms behavior probes and recall. Mitigation:
- Added minimum context checks in `_has_sufficient_context()`.
- Clarification step asks for job role/level/purpose if missing.

### Comparison matching ambiguity
Comparison requests may not contain exact catalog names. Mitigation:
- Attempt matching via simple term overlap, and if fewer than 2 matches are found, request clarification.

## 6) AI tools used

No external AI tools are used in this baseline implementation. The system relies on deterministic parsing and catalog-based ranking.

(If you later switch to RAG/LLM prompting, the evaluation report should describe prompt design, retrieval augmentation, and measured improvements.)

