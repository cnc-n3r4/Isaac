# QueryClassifier ML Upgrade - Refactor Opportunity

**Priority:** Low (heuristics work well, but ML would be more robust)  
**Effort:** Medium (2-3 hours)  
**Benefit:** Higher accuracy, fewer misclassifications  

---

## Current State

**File:** `isaac/ai/query_classifier.py`

**Current Approach:** Heuristic-based classification
- Keyword matching (geographic, info keywords)
- Regex patterns (file extensions, paths)
- Simple rule-based logic

**Works well for:**
- Clear queries: "where is alaska?" vs "where is alaska.exe?"
- Obvious patterns: File extensions, path separators
- Common cases: "what is X?", "explain Y"

**Struggles with:**
- Ambiguous queries: "show me alaska" (file or info?)
- Compound queries: "explain alaska.exe behavior"
- Context-dependent: "alaska status" (file or state?)

---

## Proposed Enhancement

### Phase 1: Add Confidence Scoring (30 min)

**Current:**
```python
def classify(self, query: str) -> QueryType:
    # Returns single classification
    return 'geographic'
```

**Proposed:**
```python
def classify(self, query: str) -> tuple[QueryType, float]:
    # Returns classification + confidence
    return ('geographic', 0.85)
```

**Benefits:**
- Fallback when confidence < threshold
- User notification for ambiguous queries
- Better debugging

---

## Phase 2: Feature Engineering (1 hour)

**Add Features:**
```python
def _extract_features(self, query: str) -> dict:
    return {
        'has_file_extension': bool,
        'has_path_separator': bool,
        'word_count': int,
        'has_action_verb': bool,      # NEW
        'has_question_word': bool,    # NEW
        'has_technical_term': bool,   # NEW
        'starts_with_show': bool,     # NEW
        'ends_with_question': bool    # NEW
    }
```

**Verb Detection:**
- Action verbs → shell_command ("list", "show", "find")
- Info verbs → general_info ("explain", "describe", "define")

**Question Words:**
- "where" + file → file_lookup
- "where" + no file → geographic
- "what" → general_info
- "how" → general_info

---

## Phase 3: Simple ML Classifier (1-2 hours)

**Option A: Naive Bayes (Simple)**
```python
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import CountVectorizer

class MLQueryClassifier:
    def __init__(self):
        self.vectorizer = CountVectorizer()
        self.classifier = MultinomialNB()
        self._train()
    
    def _train(self):
        # Training data from common queries
        queries = [...]
        labels = [...]
        X = self.vectorizer.fit_transform(queries)
        self.classifier.fit(X, labels)
```

**Option B: Zero-Shot with AI (No Training)**
```python
def classify_with_ai(self, query: str) -> tuple[QueryType, float]:
    # Ask xAI to classify
    prompt = f"""Classify this query:
    Query: {query}
    
    Types: geographic, file_lookup, shell_command, general_info
    
    Respond: type,confidence"""
    
    response = xai_client.chat(prompt)
    # Parse and return
```

---

## Trade-offs

### Heuristics (Current)
✅ Fast (<5ms)  
✅ No dependencies  
✅ Deterministic  
✅ No training data needed  
❌ Limited accuracy on edge cases  
❌ Hard to extend  

### ML Classifier
✅ Higher accuracy  
✅ Learns from mistakes  
✅ Handles edge cases  
❌ Requires training data  
❌ Slower (~20-50ms)  
❌ Adds dependencies (sklearn)  

### AI-Based Classification
✅ Highest accuracy  
✅ No training needed  
✅ Handles novel queries  
❌ Slowest (~500ms API call)  
❌ Costs API tokens  
❌ Requires network  

---

## Recommendation

**Short-term:** Add confidence scoring (Phase 1)  
- Low effort, immediate value
- Enables fallback logic
- Better debugging

**Medium-term:** Feature engineering (Phase 2)  
- Improves heuristics without ML overhead
- Still fast (<10ms)
- Easy to maintain

**Long-term:** Hybrid approach  
- Heuristics for common cases (fast)
- ML for ambiguous cases (accurate)
- AI as final fallback (comprehensive)

```python
def classify(self, query: str) -> tuple[QueryType, float]:
    # Try heuristics first
    type, confidence = self._heuristic_classify(query)
    
    if confidence > 0.8:
        return type, confidence
    
    # Fall back to ML
    type, confidence = self._ml_classify(query)
    
    if confidence > 0.6:
        return type, confidence
    
    # Final fallback: Ask AI
    return self._ai_classify(query)
```

---

## Files to Modify

1. `isaac/ai/query_classifier.py` - Add confidence scoring + features
2. `isaac/ai/query_classifier_ml.py` - NEW: ML classifier (optional)
3. `tests/test_query_classifier.py` - Update tests for confidence scores

---

## Not Urgent

Current heuristics work well for 90%+ of queries. This is a quality-of-life improvement, not a bug fix.

**Trigger to implement:**
- User reports misclassifications
- Need for production metrics
- Want to support more query types

---

**Note drafted for future reference.**</content>
<parameter name="filePath">c:\Projects\Isaac-1\.claude\to_refactor\query_classifier_ml_upgrade.md