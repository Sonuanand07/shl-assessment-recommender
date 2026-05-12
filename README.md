# SHL Assessment Recommender API

**Production-ready conversational agent for discovering SHL assessments through natural dialogue.**

A stateless FastAPI service that helps hiring managers navigate 564 SHL assessments through intelligent conversation. The agent clarifies vague needs, provides targeted recommendations, handles refinements, and compares options using grounded catalog data only.

## Quick Start

### Local Development
```bash
pip install -r requirements.txt
python start.py
python integration_test.py  # 6 tests, all passing
```

### Render Deployment
1. Push to GitHub
2. Create web service on Render.com
3. Connect repository: `shl-assessment-recommender`
4. Auto-deploys on push; ~1-2 min cold start

## API Specification

### Endpoints

**GET /health** - Service readiness
```json
Response: {"status": "ok"}
```

**POST /chat** - Main conversation endpoint
```json
Request:
{
  "messages": [
    {"role": "user", "content": "Senior Java developers, selection"},
    {"role": "assistant", "content": "Here are 5 technical assessments..."}
  ]
}

Response:
{
  "reply": "For Java developer selection, here are 5 relevant assessments...",
  "recommendations": [
    {
      "name": "Java 8 (New)",
      "url": "https://www.shl.com/products/product-catalog/view/java-8-new/",
      "test_type": "K",
      "keys": ["Knowledge & Skills"],
      "duration": "45 mins",
      "languages": ["English"]
    }
  ],
  "end_of_conversation": false
}
```

**Response Fields:**
- `reply`: Natural language from agent
- `recommendations`: Array of 0-10 assessments (empty during clarification)
- `end_of_conversation`: Boolean (true only when task complete)

## Design & Architecture

**Stateless Conversation**: Each request carries full history; agent reconstructs context from scratch.

**Rule-Based, No LLM**: Deterministic keyword extraction + multi-factor scoring. No external API calls.

**Multi-Factor Scoring**:
- Assessment type match: +20 pts (highest priority)
- Job level match: +10 pts
- Skill keyword match: +5 pts
- Job title match: +3 pts

**Robust Catalog Loading**: Three-tier fallback (standard JSON → control-char removal → line-by-line parsing) loads all 564 items despite encoding issues.

**Conversation Flow**:
1. Extract context (job title, level, type, skills)
2. Check sufficiency (have enough info?)
3. Route: clarify OR refuse OR recommend
4. Score & rank all 564 items
5. Return top-10 with catalog URLs

## Installation & Setup

```bash
# Clone/navigate to project directory
cd "d:\SHL Assesment Project"

# Install dependencies (Python 3.11+)
pip install -r requirements.txt

# Start server (runs on http://localhost:8000)
python start.py

# In another terminal, run tests
python integration_test.py
```

**API Documentation**:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing & Evaluation

**6 Integration Tests - All Passing ✅**

1. Health Check - Service readiness
2. Simple Conversation - Senior developer hiring
3. Multi-Turn Conversation - Entry-level contact center with refinements
4. Personality Assessments - 7/10 recommendations are personality-focused
5. Off-Topic Refusal - General hiring advice properly rejected
6. Vague Query Handling - Insufficient context properly detected

**Run Tests**:
```bash
python integration_test.py
# Output: ✓ All 6 tests passed!
```

**Evaluation Criteria** (per assignment):
- Hard Evals: Schema compliance, catalog-only URLs, 8-turn max
- Recall@10: Relevant assessments in top-10 recommendations
- Behavior Probes: Off-topic refusal, no premature recommendations, refinement support

## Deployment

### Render.com (Recommended)

**Automatic Deployment**:
1. Push code to GitHub
2. Create web service on render.com
3. Connect repository: `Sonuanand07/shl-assessment-recommender`
4. Auto-deploys on every push
5. Available at: `https://shl-assessment-recommender.onrender.com`

**Configuration**:
- Build: `pip install -r requirements.txt`
- Start: `python -m uvicorn app:app --host 0.0.0.0 --port $PORT`
- Python: 3.11+
- Plan: Free (or Starter)

**Performance**:
- Cold start: ~1-2 min (free tier, after 30 min inactivity)
- Warm requests: <500ms
- All 6 tests pass

### Verify Deployment

```bash
# Health check
curl https://shl-assessment-recommender.onrender.com/health
# Response: {"status": "ok"}

# API docs
https://shl-assessment-recommender.onrender.com/docs
```

## File Structure

```
d:\SHL Assesment Project\
├── app.py                      # FastAPI service (137 lines)
├── agent.py                    # Conversational logic (350+ lines)
├── catalog.py                  # Catalog loading (180 lines)
├── config.py                   # Configuration (20 lines)
├── start.py                    # Server launcher (25 lines)
├── requirements.txt            # Python dependencies
├── Procfile                    # Heroku/Render config
├── render.yaml                 # Render service config
├── runtime.txt                 # Python 3.11.9
├── integration_test.py         # 6 integration tests (200+ lines)
├── shl_product_catalog.json    # 564 SHL assessments
├── README.md                   # This file
├── APPROACH.md                 # Design document (410 lines)
├── DEPLOYMENT.md               # Deployment guide (186 lines)
└── SHL_sample_conversations/   # C1-C10 reference traces
```

## Dependencies

```
fastapi>=0.136.0           # Web framework
uvicorn[standard]>=0.46.0  # ASGI server
requests>=2.33.0           # HTTP client
python-dotenv>=1.0.0       # Environment variables
```

**Install**: `pip install -r requirements.txt`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 8000 in use | `taskkill /PID <pid> /F` then restart |
| Catalog not loading | Verify `shl_product_catalog.json` in project root |
| Tests fail | Ensure server running on localhost:8000 |
| "python: command not found" on Render | Using `render.yaml` instead of Procfile |

## Conversational Examples

**Clarification Flow**
```
User: "We need an assessment"
Agent: "Let's start by understanding your hiring need. What role are you filling?"
```

**Recommendation Flow**
```
User: "Senior Java developers, selection"
Agent: "For Java developer selection, here are 7 technical assessments..."
Recommendations: [Java 8 (New), Problem Solving, ...]
```

**Refinement Flow**
```
User: "Actually, add personality tests"
Agent: "Got it, here are 8 assessments with personality tests included..."
```

**Off-Topic Refusal**
```
User: "What's the best hiring advice?"
Agent: "I'm focused on SHL assessment recommendations. I can't help with general hiring advice..."
```

## Submission Details

**Public API**: https://shl-assessment-recommender.onrender.com

**Approach Document**: [APPROACH.md](./APPROACH.md) - 410 lines covering design, retrieval, evaluation, lessons learned

**Test Status**: ✅ 6/6 passing (100%)

**Catalog**: ✅ 564/564 items loaded

**Features Implemented**:
- ✅ Clarification (progressive questions)
- ✅ Recommendations (1-10 assessments with URLs)
- ✅ Refinement (mid-conversation updates)
- ✅ Comparison (assessment data included)
- ✅ Refusal (off-topic detection)
- ✅ Schema compliance (exact format)

**Architecture**:
- No external LLM calls (rule-based)
- Stateless design (scales infinitely)
- Deterministic scoring (reproducible)
- Robust parsing (handles catalog encoding issues)

**AI Tools Used**: GitHub Copilot (code generation, testing, documentation)

## Support

**Documentation**:
- [APPROACH.md](./APPROACH.md) - Full design rationale
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Detailed deployment guide
- `/docs` endpoint - Interactive Swagger UI

**Sample Conversations**: `SHL_sample_conversations/GenAI_SampleConversations/` (C1-C10)

**Issues**:
1. Check README & APPROACH.md thoroughly
2. Review sample conversation traces
3. Run integration tests locally
4. Check server logs for error messages

---

**Status**: ✅ Production Ready  
**Tests**: ✅ 6/6 Passing  
**Deployment**: ✅ Render Ready  
**Documentation**: ✅ Complete
