# Deployment & Submission Guide

## Quick Deployment to Render

### Option 1: Automatic Deployment (Recommended)

1. **Connect GitHub Repository**
   - Go to https://render.com
   - Sign up / log in
   - Click "New" → "Web Service"
   - Connect GitHub account and select `shl-assessment-recommender`

2. **Configure Service**
   - **Name**: `shl-assessment-recommender`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python3 -m uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free (or Starter if on free tier limit)
   - **Root Directory**: `.` (project root)

3. **Deploy**
   - Click "Create Web Service"
   - Render will automatically build and deploy
   - Wait 1-2 minutes for cold start
   - Copy the public URL (e.g., `https://shl-assessment-recommender-xxxxx.onrender.com`)

### Option 2: Manual Build & Deploy

```bash
# Test locally first
python3 start.py
# Or: python -m uvicorn app:app --host 0.0.0.0 --port 8000
# Visit http://localhost:8000/health
# Should return: {"status": "ok"}

# Run tests
python3 integration_test.py
# All 6 tests should pass

# Deploy to Render using web dashboard
# See Option 1 above
```

---

## Verifying Deployment

Once deployed to Render (wait 1-2 minutes for cold start):

```bash
# Test health endpoint
curl https://shl-assessment-recommender-xxxxx.onrender.com/health
# Expected: {"status": "ok"}

# Test chat endpoint
curl -X POST https://shl-assessment-recommender-xxxxx.onrender.com/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{
      "role": "user",
      "content": "We need personality assessments for senior leadership."
    }]
  }'
# Expected: Personality assessments in top 10 recommendations
```

---

## Assignment Form Submission

### Question 1: "Did your solution meet all following expectations?"
**Answer**: YES

**Evidence**:
- ✅ Built API using FastAPI with `/health` and `/chat` endpoints
- ✅ Handles clarification (asks for missing context progressively)
- ✅ Returns relevant recommendations from SHL catalog
- ✅ Supports refinement (users can ask follow-up questions)
- ✅ Compares assessments using catalog evidence (duration, languages, job levels)
- ✅ Includes evaluation methods (6 integration tests, 100% pass rate)

### Question 2: "Provide public base URL"
**Answer**: `https://shl-assessment-recommender.onrender.com`

(Will update once Render deployment completes)

### Question 3: "Does your solution have a cold-start delay?"
**Answer**: YES, 1-2 minutes

**Why**: Free Render tier uses serverless architecture that spins down after inactivity. First request after idle period triggers rebuild.

**Impact**: Negligible for production use; typically only occurs after >30 minutes of no traffic.

### Question 4: "Did you use any LLM (Large Language Model)?"
**Answer**: NO

**Approach**: Rule-based system using:
- Regex-based context extraction
- Keyword matching against assessment types
- Multi-factor scoring algorithm
- Stateless conversation flow

**Rationale**: Deterministic logic with full transparency; no API dependency; faster response times; predictable costs.

### Question 5: "Which AI tools did you use?"
**Answer**: GitHub Copilot

**Usage**:
- Code generation for API endpoints and data models
- Test case development (integration_test.py)
- Documentation and docstring generation
- Debugging assistance

### Question 6: "Approach Document"
**File**: APPROACH.md (this repository)

**Contents**:
1. Design choices (stateless API, rule-based agent, multi-factor scoring)
2. Retrieval setup (keyword matching, structured filtering)
3. Prompt design (conversation templates, state machine)
4. Evaluation methods (6 integration tests, sample conversation validation)
5. What worked (determinism, progressive clarification, robust data handling)
6. What didn't work (LLM integration reasons, embedding trade-offs)
7. Lessons learned (scoring weight tuning, keyword coverage, deployment tips)
8. Deployment & operations guide
9. Future improvements

---

## Key Submission Files

| File | Purpose | For Submission |
|------|---------|---|
| `app.py` | FastAPI service | ✅ Public GitHub |
| `agent.py` | Conversational logic | ✅ Public GitHub |
| `catalog.py` | Data layer | ✅ Public GitHub |
| `requirements.txt` | Dependencies | ✅ Public GitHub |
| `Procfile` | Render configuration | ✅ Public GitHub |
| `integration_test.py` | Test suite (6/6 passing) | ✅ Public GitHub |
| `README.md` | User documentation | ✅ Public GitHub |
| `APPROACH.md` | Design & approach document | ✅ Attach to form or include link |

---

## Submission Checklist

- [ ] API deployed on Render
- [ ] `/health` endpoint returns `{"status": "ok"}`
- [ ] `/chat` endpoint accepts conversation messages
- [ ] All 6 integration tests passing
- [ ] Public GitHub repository with all source code
- [ ] APPROACH.md document completed
- [ ] Assignment form filled with answers above
- [ ] Public API URL copied to submission form
- [ ] Sample conversations validated (C1-C10)

---

## Troubleshooting

### API not responding from Render

1. Check build logs on Render dashboard
2. Verify Python version is 3.11+ (check runtime.txt)
3. Ensure requirements.txt includes: fastapi, uvicorn[standard]
4. Verify Procfile contains: `python3 -m uvicorn app:app --host 0.0.0.0 --port $PORT` (note: python3, not python)
5. Check Render doesn't have open ports detected—this means app isn't binding to PORT correctly

### Personality assessments not in recommendations

1. Run local test: `python integration_test.py`
2. Check agent.py: ASSESSMENT_TYPE_MAPPING should include "personality" keyword
3. Verify scoring: Assessment type match should be +20 points (highest priority)

### Catalog not loading

1. Check shl_product_catalog.json exists in project root
2. Run locally: `python start.py` and check startup logs
3. Test: `curl http://localhost:8000/health`

---

## Support

For issues or questions about deployment:
1. Check README.md for detailed API documentation
2. Review APPROACH.md for design rationale
3. Examine integration_test.py for example usage
4. Review app.py, agent.py comments for code-level documentation
