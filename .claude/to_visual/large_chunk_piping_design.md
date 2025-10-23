# Large Chunk Piping Design Issue

## Problem Statement

When piping `/mine dig` results to `/ask`, collection chunks can be massive (user-configurable chunk size in xAI console). This creates:

1. **Token limit issues** - May exceed Grok's context window
2. **Timeout correlation** - Large payloads contribute to 10s gRPC timeout
3. **Cost concerns** - Larger prompts = expensive API calls
4. **Relevance dilution** - Too much context overwhelms the AI

## Current Behavior

```python
# /mine dig returns full chunk content
return f"Answer: {match.chunk_content}"  # Could be 5000+ characters

# /ask receives it all
query = f"{user_question}\n\nContext data:\n{input_content}"  # Massive prompt
```

## Design Options

### Option 1: Truncate in /mine (Simple)
**Pros:**
- Easy to implement
- Predictable output size
- Works for all pipe consumers

**Cons:**
- Might cut off important information
- User loses access to full content
- One-size-fits-all approach

```python
def _handle_dig(self, args: List[str]) -> str:
    # ...search...
    if match.chunk_content:
        content = match.chunk_content
        if len(content) > 2000:  # Truncate for piping-friendly output
            content = content[:2000] + "\n... [truncated]"
        return f"Answer: {content}"
```

### Option 2: Smart Truncation in /ask (Adaptive)
**Pros:**
- /mine stays unchanged
- /ask controls its own input size
- Can use different strategies per AI provider

**Cons:**
- More complex logic
- /ask needs to know token limits

```python
def _handle_chat_query(query: str, config: dict, session: SessionManager, is_piped_input: bool = False) -> str:
    # Detect large piped content
    if is_piped_input and len(query) > 10000:  # ~3000 tokens
        # Extract user question and context
        parts = query.split("\n\nContext data:\n", 1)
        if len(parts) == 2:
            user_question = parts[0]
            context = parts[1]
            
            # Truncate context intelligently
            if len(context) > 8000:
                context = context[:8000] + "\n\n... [Context truncated - original was too large]"
            
            query = f"{user_question}\n\nContext data:\n{context}"
    
    # Continue normal flow...
```

### Option 3: Multi-Match Summary (Rich)
**Pros:**
- Returns multiple relevant chunks with scores
- User sees what was found
- Better context for AI

**Cons:**
- More complex output format
- Changes /mine dig behavior significantly

```python
def _handle_dig(self, args: List[str]) -> str:
    # ...search...
    if response.matches:
        # Return top 3 matches with metadata
        result = f"Found {len(response.matches)} matches:\n\n"
        for i, match in enumerate(response.matches[:3], 1):
            content = match.chunk_content[:500]  # Preview only
            score = getattr(match, 'score', 'N/A')
            result += f"Match {i} (score: {score}):\n{content}...\n\n"
        return result
```

### Option 4: Piping-Aware Mode Flag (Flexible)
**Pros:**
- /mine can detect when piped and adjust output
- Best of both worlds
- User gets full content when not piped

**Cons:**
- /mine needs to know if it's being piped
- More complex implementation

```python
def main():
    # Detect if we're in a pipe chain
    in_pipe = not sys.stdin.isatty()  # Being piped TO
    will_pipe = ???  # How to detect piping OUT?
    
    # Pass mode to handler
    handler = MineHandler(session)
    result = handler.handle_command(args, command, piped_mode=will_pipe)
```

## Recommended Approach

**Hybrid: Option 2 + Option 3**

1. **In /mine dig:** Return top 3 matches with truncated previews (500 chars each)
2. **In /ask:** Smart truncation for safety (10k char limit)
3. **Add /mine dig --full flag:** For when user wants complete content

This gives:
- Safe defaults for piping
- Rich context (multiple matches)
- Escape hatch for full content
- /ask protection against oversized input

## Implementation Priority

**Phase 1 (Immediate):**
- Add smart truncation in /ask for large piped content
- Prevents token limit errors
- Non-breaking change

**Phase 2 (Next):**
- Modify /mine dig to return multi-match summaries
- Add --full flag for complete content
- Better piping experience

**Phase 3 (Future):**
- Add /mine dig --format=json for structured output
- Support for different output modes (summary, full, json)
- Piping-aware auto-detection

## Token Budget Estimates

Grok-3 context window: ~128k tokens (~400k characters)

**Current risk:**
- User question: ~50 tokens
- "Context data:" wrapper: ~10 tokens  
- Chunk content: **UNKNOWN** - could be 1k-50k+ tokens
- System prompt: ~500 tokens
- **Total: Could exceed limits**

**Safe targets:**
- Piped content limit: 8000 chars (~2500 tokens)
- Multi-match: 3 matches × 500 chars = 1500 chars (~500 tokens)
- System prompt: ~500 tokens
- User question: ~50 tokens
- **Total: ~3k tokens - safe**

## User Control

Add config option:
```json
{
  "piping": {
    "max_chunk_size": 8000,
    "multi_match_count": 3,
    "match_preview_length": 500
  }
}
```

## Open Questions

1. **How to detect chunk size from xAI API?** - Not available programmatically
2. **Should /mine always summarize?** - Maybe only when piped
3. **What about /mine dig --raw for debugging?** - Good idea
4. **Does xAI SDK support limiting match count?** - Yes, can pass `top_k` parameter

---

**Next Steps:**
1. Implement Phase 1 smart truncation in /ask
2. Test with large collection chunks
3. Monitor for token limit errors
4. Plan Phase 2 multi-match support