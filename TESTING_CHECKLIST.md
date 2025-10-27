# 🧪 TESTING CHECKLIST - Stages 1 & 2

## ⚠️ **CRITICAL ISSUES FOUND & FIXED**

### Issue #1: MongoDB Collection Initialization ✅ FIXED
**Problem**: `get_collection()` was called in `__init__` (synchronous context)
**Fix**: Converted to lazy-loaded properties
**File**: `backend/app/services/misconception_service.py`

---

## 📋 **PRE-FLIGHT CHECKS** (Before Starting Docker)

### Static Analysis
- [ ] Run import validation: `python misconception_stem_rag/test_implementation.py`
- [ ] Check for syntax errors in new files
- [ ] Verify all imports resolve correctly

### File Existence
- [ ] `backend/app/services/semantic_search.py` exists
- [ ] `backend/app/services/misconception_service.py` exists  
- [ ] `backend/app/routes/admin.py` exists
- [ ] `data/misconceptions/physics_misconceptions.csv` exists

---

## 🐳 **DOCKER TESTING** (Requires Docker Desktop)

### 1. Start Services
```powershell
# Start Docker Desktop manually first!
docker-compose up -d
docker logs adaptive_api --tail 50  # Check for startup errors
```

**Expected Output**:
- ✅ No import errors
- ✅ "Semantic search service initialized"
- ✅ ChromaDB client initialized
- ✅ MongoDB connected

**Potential Issues**:
- ❌ `ModuleNotFoundError: No module named 'sentence_transformers'`
  - **Fix**: Rebuild Docker image with new requirements
- ❌ `chromadb connection error`
  - **Fix**: Check ChromaDB path in config

---

### 2. Test Stage 1: Semantic Search

#### Upload PDF (Triggers Embedding)
```bash
curl -X POST http://localhost:8000/pdf-v2/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.pdf"
```

**Check Logs**:
```powershell
docker logs adaptive_api -f | Select-String -Pattern "embedding|semantic|chroma"
```

**Expected**:
- ✅ "🔄 Embedding X PDF chunks..."
- ✅ "✅ Stored X chunks in ChromaDB collection 'pdf_session_XXX'"
- ✅ Sentence-transformer model loads (first time only ~90MB download)

**Potential Issues**:
- ❌ "Failed to download sentence-transformer model"
  - **Cause**: Docker container can't access internet
  - **Fix**: Pre-download model or check network
- ❌ "ChromaDB path not writable"
  - **Cause**: Permission issues
  - **Fix**: Check docker-compose volume mounts

#### Generate Questions (Uses Semantic Retrieval)
```bash
curl -X POST http://localhost:8000/pdf-v2/sessions/SESSION_ID/generate-questions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "sess_XXX", "selected_topics": ["Topic 1"], "num_questions_per_topic": 2}'
```

**Check Logs**:
```powershell
docker logs adaptive_api -f | Select-String -Pattern "semantic search|RAG|relevant chunks"
```

**Expected**:
- ✅ "🔍 Semantic search for topic: 'Topic Name'"
- ✅ "✅ Retrieved 5 relevant chunks for 'Topic Name'"
- ✅ "📄 Using X chars of semantically retrieved content"
- ✅ "✅ Generated question 1/2 for Topic Name using RAG"

---

### 3. Test Stage 2: Misconception Database

#### Seed Misconceptions from CSV
```bash
curl -X POST http://localhost:8000/admin/seed-misconceptions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"csv_files": ["physics_misconceptions.csv"]}'
```

**Expected Response**:
```json
{
  "total_seeded": 3,
  "files_processed": 1,
  "results": [
    {
      "file": "physics_misconceptions.csv",
      "status": "success",
      "count": 3
    }
  ]
}
```

**Check Logs**:
```powershell
docker logs adaptive_api -f | Select-String -Pattern "misconception|seeding"
```

**Expected**:
- ✅ "📄 CSV headers: ['subject', 'concept', 'misconception_text', 'correction']"
- ✅ "📚 Inserted 3 misconceptions into MongoDB"
- ✅ "✅ Seeded 3 misconceptions from physics_misconceptions.csv"

**Potential Issues**:
- ❌ "CSV file not found"
  - **Fix**: Check `data/misconceptions/` path in container
- ❌ "Unsupported CSV format"
  - **Fix**: Verify CSV headers match expected format

#### View Statistics
```bash
curl http://localhost:8000/admin/misconception-stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected Response**:
```json
{
  "total_validated": 3,
  "total_csv_seeded": 3,
  "total_ai_generated": 0,
  "total_from_user_feedback": 0,
  "by_subject": [
    {"subject": "physics", "count": 3}
  ]
}
```

---

## 🔬 **FUNCTIONAL TESTING**

### End-to-End Test: PDF Upload → Question Generation

1. **Register/Login** to get JWT token
2. **Upload PDF** → Verify ChromaDB embedding happens
3. **Select Topics** from extracted topics
4. **Generate Questions** → Verify semantic retrieval
5. **Take Quiz** → Submit answers
6. **Check Feedback** → Verify misconception mining (Stage 3)

---

## 🐛 **KNOWN ISSUES & WORKAROUNDS**

### Issue: Sentence-Transformers Model Download
- **Symptom**: "Downloading all-MiniLM-L6-v2..." takes 2-3 minutes first time
- **Not a bug**: Model is ~90MB, cached after first download
- **Location**: Inside Docker container (not on host)

### Issue: ChromaDB Persistence
- **Symptom**: ChromaDB collections lost after container restart
- **Check**: Verify `chroma_db/` volume mount in docker-compose
- **Fix**: Ensure persistent volume configured

### Issue: MongoDB Async Operations
- **Fixed**: Lazy-loaded collections in MisconceptionService
- **Verify**: No errors about "coroutine was never awaited"

---

## ✅ **SUCCESS CRITERIA**

### Stage 1: Semantic Search
- [ ] PDF chunks embedded in ChromaDB on upload
- [ ] Semantic search retrieves top 5 relevant chunks per topic
- [ ] Question generation uses retrieved context (check logs for "using RAG")
- [ ] ChromaDB collections persist across container restarts

### Stage 2: Misconception Database
- [ ] CSV seeding works (3 physics misconceptions loaded)
- [ ] Misconceptions stored in MongoDB
- [ ] Misconceptions embedded in ChromaDB for semantic search
- [ ] Statistics endpoint returns correct counts
- [ ] Both CSV formats supported (legacy + new)

---

## 📊 **PERFORMANCE BENCHMARKS**

### Expected Timing:
- PDF Upload (10 pages): 5-10 seconds (including embedding)
- Semantic Search (per topic): <500ms
- Question Generation (2 questions): 3-5 seconds (GPT-4o calls)
- CSV Seeding (100 misconceptions): 10-15 seconds

### Memory Usage:
- Sentence-transformers model: ~200MB RAM
- ChromaDB index: ~50MB per 1000 chunks

---

## 🚀 **NEXT: Stage 3 Testing**

After Stages 1 & 2 pass:
1. Dual retrieval (facts + misconceptions)
2. Misconception mining from quiz feedback
3. Dynamic trait updates

---

**Status**: Ready for Docker testing
**Last Updated**: October 27, 2025
**Tester**: Start Docker Desktop and run tests above!
