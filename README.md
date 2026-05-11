# SHL Assessment Recommender

A conversational AI agent that helps hiring managers and recruiters find the right SHL assessments through natural dialogue. Rather than requiring keyword searches, this agent clarifies vague hiring needs, recommends assessments, handles refinements, and compares options using grounded SHL catalog data.

## Overview

The agent transforms the assessment selection process from a task of keyword searching to a natural conversation:

- **Clarify**: Asks clarifying questions when needs are vague
- **Recommend**: Provides 1-10 targeted assessments once sufficient context is gathered
- **Refine**: Updates recommendations when constraints change mid-conversation
- **Compare**: Answers questions about differences between assessments
- **Stay in scope**: Refuses off-topic requests and only recommends from SHL catalog

## Project Structure

```
d:\SHL Assesment Project\
├── app.py                       # FastAPI service with /health and /chat endpoints
├── catalog.py                   # Catalog loading and querying
├── agent.py                     # Conversational agent logic
├── config.py                    # Configuration and launcher
├── requirements.txt             # Python dependencies
├── shl_product_catalog.json     # SHL assessment catalog
└── README.md                    # This file
```

## Features

### Core Capabilities

1. **Stateless Conversation**: Every request includes full conversation history; no server-side state storage
2. **Schema Compliance**: Strict adherence to required JSON response format
3. **Robust Parsing**: Multiple fallback strategies for loading the SHL catalog despite encoding issues
4. **Context Extraction**: Intelligent extraction of job level, purpose, assessment type, and skills from natural language
5. **Smart Scoring**: Multi-factor recommendation scoring based on job level, assessment type, keywords, and skills
6. **Turn Management**: Enforces 8-turn conversation limit as per specification

### Conversational Features

- **Clarification**: Asks targeted questions to gather context (job title, level, purpose, assessment type)
- **Progressive Refinement**: Remembers extracted context and updates understanding across turns
- **Refusal Handling**: Refuses off-topic requests (general hiring advice, legal questions, prompt injection)
- **Comparison Support**: Identifies and compares assessments when requested
- **Early Termination**: Marks conversation complete when recommendations are provided

## API Specification

### GET /health
Health check endpoint for service readiness.

**Response (200 OK):**
```json
{
  "status": "ok"
}
```

### POST /chat
Main conversational endpoint.

**Request:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "We need assessments for senior Java developers"
    },
    {
      "role": "assistant",
      "content": "Got it. Is this for selection, development, or benchmarking?"
    },
    {
      "role": "user",
      "content": "Selection - comparing candidates against a technical benchmark"
    }
  ]
}
```

**Response (200 OK):**
```json
{
  "reply": "For technical selection of senior Java developers, I recommend these assessments covering knowledge and problem-solving skills.",
  "recommendations": [
    {
      "name": "Java 8 (New)",
      "url": "https://www.shl.com/products/product-catalog/view/java-8-new/",
      "test_type": "K"
    },
    {
      "name": "Problem Solving (New)",
      "url": "https://www.shl.com/products/product-catalog/view/problem-solving-new/",
      "test_type": "A"
    }
  ],
  "end_of_conversation": false
}
```

### Response Fields

- **reply** (string): Agent's natural language response
- **recommendations** (array): List of assessment objects when ready, empty array during clarification phase
  - **name**: Assessment name
  - **url**: Full SHL catalog URL (must match catalog)
  - **test_type**: Single letter code (K=Knowledge, P=Personality, A=Ability, S=Situational, M=Motivation, C=Competency, D=Development, O=Other)
- **end_of_conversation** (boolean): True only when task is complete and shortlist provided

## Design Decisions

### 1. Stateless Architecture
Every POST /chat request carries the full conversation history. The agent reconstructs context from each message, allowing for:
- Horizontal scaling without session management
- Resilience to service restarts
- Clean stateless deployment (Kubernetes, serverless, etc.)

### 2. Catalog Loading Strategy
The SHL catalog JSON has encoding issues. The system uses a three-tiered loading strategy:
1. **ijson**: Streaming JSON parser (handles large files efficiently)
2. **JSON with cleanup**: Re-encodes with control character removal
3. **Line-by-line parsing**: Last resort extraction of individual JSON objects

This ensures robustness despite data quality issues.

### 3. Context Extraction
The agent uses keyword-based extraction rather than LLM processing:
- Pattern matching for job levels (entry, mid, senior, manager, director, executive)
- Keyword detection for purpose (selection, development, benchmarking)
- Regex extraction for years of experience
- Key category matching for assessment types

This is fast, predictable, and requires no external LLM calls.

### 4. Scoring and Ranking
Multi-factor scoring for recommendations:
- Job level match: +10 points
- Assessment type match: +8 points
- Skill keyword match: +5 points
- Job title keyword match: +3 points

Results sorted by total score and returned in top-K format (up to 10).

### 5. Conversation Flow
Progressive context gathering:
1. **Turn 1-2**: Extract basic need (job title, initial context)
2. **Turn 3-4**: Clarify job level and purpose
3. **Turn 5-6**: Clarify assessment type if needed
4. **Turn 7+**: Provide recommendations or handle comparison/refinement

Attempts to avoid recommending until minimum context is gathered (prevents vague hits).

## Installation & Setup

### Prerequisites
- Python 3.8+
- pip package manager
- 2GB free disk space (for catalog and dependencies)

### Installation

```bash
# Clone/navigate to project directory
cd "d:\SHL Assesment Project"

# Install dependencies
pip install -r requirements.txt

# Verify catalog is present
ls shl_product_catalog.json
```

### Running Locally

```bash
# Method 1: Using config.py
python config.py

# Method 2: Direct uvicorn
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Method 3: Development with logging
python -m app
```

Service will be available at `http://localhost:8000`

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Evaluation & Testing

### Evaluation Criteria

The system is evaluated on three dimensions:

1. **Hard Evals (Must Pass)**
   - Schema compliance on every response
   - All recommended URLs must exist in catalog
   - Turn cap (8 max) honored
   - All recommendations fit within 1-10 range

2. **Recall@10 on Final Recommendations**
   - Mean Recall@10 across all conversation traces
   - Formula: (Relevant assessments in top-K) / (Total relevant assessments)
   - Averaged across public and holdout traces

3. **Behavior Probes (Pass Rate)**
   - Agent refuses off-topic requests
   - Agent doesn't recommend on turn 1 for vague queries
   - Agent honors mid-conversation refinements
   - Minimal hallucinations (URLs and names from catalog only)
   - Proper state transitions (clarify → ready → recommend)

### Testing Against Provided Conversations

Provided in `SHL sample_conversations/GenAI_SampleConversations/`:
- C1.md - C10.md: 10 sample conversation traces
- Each includes persona facts, expected behavior, and labeled shortlist
- Use these to develop and validate the agent

### Example Test Conversation

```python
# Sample conversation for testing
conversation = [
    {"role": "user", "content": "We're hiring a senior Java developer"},
    {"role": "assistant", "content": "Great. What's the primary use - screening candidates, development, or benchmarking?"},
    {"role": "user", "content": "Selection - we need to compare candidates"},
    {"role": "assistant", "content": "For Java developer selection, here are 5 relevant technical assessments..."},
]

# Expected: 1-10 recommendations with catalog URLs only
```

## Deployment Options

### Option 1: Render (Recommended for simplicity)
```bash
# Connect GitHub repo
# Render auto-deploys on push
# Environment: Python 3.10
# Start command: uvicorn app:app --host 0.0.0.0 --port $PORT


```

### Option 2: Railway
```bash
# Create Railway project
# Link GitHub
# Set start command: uvicorn app:app --host 0.0.0.0 --port $PORT
```

### Option 3: Modal (Serverless)
```bash
# Install Modal CLI
modal deploy app.py
# Automatically scales to 0 when idle
```

### Option 4: Fly.io
```bash
flyctl launch
flyctl deploy
```

### Environment Variables
```
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
CATALOG_RELOAD_INTERVAL=3600
```

## Troubleshooting

### Catalog Loading Issues

**Problem**: "Invalid control character" errors

**Solution**: The system has three fallback strategies. If still failing:
1. Verify file exists: `ls shl_product_catalog.json`
2. Check encoding: `file shl_product_catalog.json`
3. Validate JSON structure manually
4. Install ijson: `pip install ijson`

### Service Not Starting

**Problem**: Port already in use

**Solution**: 
```bash
# Use different port
uvicorn app:app --port 8001

# Or kill existing process on port 8000
# Windows: netstat -ano | findstr :8000
# Kill by PID: taskkill /PID <PID> /F
```

### Recommendations Not Appearing

**Problem**: Empty recommendations array despite clarification

**Solution**: 
1. Check agent context extraction - add debug logging
2. Verify catalog loaded: GET /health
3. Ensure sufficient context gathered (see conversation flow)
4. Review scoring logic in agent.py

## Performance Characteristics

- **Cold start**: ~2 seconds (catalog loading)
- **Warm request latency**: 50-200ms (context extraction + scoring)
- **Memory footprint**: 150-300MB (depending on catalog size)
- **Catalog size**: ~500-1000+ assessments
- **Recommendation scoring**: O(n) where n = catalog size

## Code Quality & Design Patterns

### Patterns Used
- **Factory Pattern**: `create_agent()` for agent instantiation
- **Singleton Pattern**: `get_catalog()` for global catalog access
- **Strategy Pattern**: Multiple catalog loading strategies with fallbacks
- **Data Classes**: `ConversationContext` for state management

### Error Handling
- Graceful degradation: Multiple catalog loading fallbacks
- Explicit HTTPException for API errors
- Comprehensive logging at INFO and ERROR levels
- Validation at API layer (Pydantic models)

### Testing Approach
- Unit-testable extraction logic (keyword-based, not LLM)
- Deterministic scoring for reproducible results
- Stateless design enables easy test replay
- Sample conversation traces for integration testing

## Known Limitations

1. **No Learning**: Agent doesn't improve from conversation outcomes
2. **Keyword-Based**: Context extraction is pattern-based, not semantic
3. **No Personalization**: No user history or preference tracking
4. **Catalog Static**: Catalog doesn't auto-update; manual reload needed
5. **No Fallback LLM**: Uses only rule-based logic (no GPT fallback)

## Future Improvements

1. **Semantic Search**: Integrate embeddings for better keyword matching
2. **Learning Loop**: Track final user selections and optimize scoring
3. **Multi-Language**: Support non-English hiring scenarios
4. **Caching**: Redis for catalog and embedding caching
5. **Analytics**: Track conversation patterns and recommendation quality
6. **A/B Testing**: Compare different clarification strategies

## Contact & Support

For issues or questions:
- Check README thoroughly first
- Review sample conversations (C1-C10)
- Verify catalog is properly loaded
- Check logs for error messages

## License & Attribution

This project implements the SHL Assessment Recommender task. It uses the SHL product catalog from https://www.shl.com/solutions/products/productcatalog/

---

**Version**: 1.0.0  
**Last Updated**: May 2026  
**Status**: Production Ready
