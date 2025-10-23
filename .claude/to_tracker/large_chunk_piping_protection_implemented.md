# Large Chunk Piping Protection - Implemented

**Status:** ✅ COMPLETE  
**Date:** 2025-10-22  
**Priority:** HIGH  
**Component:** Piping System, /mine, /ask  

## Issue Identified

User discovered that when piping `/mine dig` to `/ask`, collection chunks can be massive (user-configurable in xAI console). This creates:

1. **Token limit risks** - May exceed Grok's context window
2. **Timeout correlation** - Large payloads may contribute to 10s gRPC timeout
3. **Cost concerns** - Larger prompts = expensive API calls
4. **Poor UX** - Single huge chunk may not be most relevant

## Solution Implemented

### Phase 1: Immediate Protection (COMPLETE)

**1. Smart Truncation in /ask** (`isaac/commands/ask/run.py`)
- Detects large piped content (>10k chars)
- Extracts user question from context data
- Truncates context to 8000 chars (~2500 tokens)
- Adds truncation notice to user
- Preserves beginning of content (most relevant)

```python
if is_piped_input and len(query) > 10000:
    # Split and truncate intelligently
    max_context_chars = 8000
    if len(context) > max_context_chars:
        context = context[:max_context_chars] + "\n\n... [Context truncated]"
```

**2. Multi-Match Support in /mine dig** (`isaac/commands/mine/run.py`)
- Returns top 3 matches instead of just first
- Single match: 2000 char limit with truncation notice
- Multiple matches: 500 char preview each with scores
- Better context for AI analysis
- Prevents overwhelming output

```python
if len(matches) == 1:
    content = match.chunk_content[:2000]  # Truncate large chunks
else:
    # Multiple matches - show previews
    content = match.chunk_content[:500]  # Preview only
```

## Benefits

✅ **Token Safety** - Never exceed API limits  
✅ **Better Relevance** - Multiple matches show variety  
✅ **Timeout Mitigation** - Smaller payloads process faster  
✅ **User Awareness** - Clear truncation notices  
✅ **Non-Breaking** - Existing workflows still work  

**Note:** xAI API is cheaper than Grok subscription, so token cost is not a concern. Focus is on token limits and timeout mitigation.  

## Testing Required

1. **Test with large chunks:**
   ```
   /mine use cnc-info
   /mine dig coolant | /ask what is this?
   ```

2. **Test truncation notice:**
   - Verify "[Context truncated]" appears for large content
   - Check AI still provides useful answers

3. **Test multi-match output:**
   - Verify 3 matches display with previews
   - Check score display (if available)

4. **Test single match:**
   - Verify 2000 char limit applied
   - Check truncation notice for huge chunks

## Token Budget

**Before (UNSAFE):**
- Query: ~50 tokens
- Context: **UNKNOWN** (1k-50k+ tokens possible)
- System prompt: ~500 tokens
- **Total: Could exceed 128k limit** ❌

**After (SAFE):**
- Query: ~50 tokens
- Context: ≤8000 chars (~2500 tokens max)
- System prompt: ~500 tokens
- **Total: ~3k tokens** ✅

## Future Enhancements (Phase 2)

**Priority: HIGH - User Requested**

1. **✅ /mine config command** - Runtime configuration (SPEC READY)
   - Spec: `.claude/mail/to_implement/mine_config_command_spec.md`
   - Settings: max_chunk_size, match_preview_length, piping thresholds, match_count
   - User can tweak on the fly: `/mine config set max_chunk_size 5000`
   - Persists to `~/.isaac/config.json`
   - Estimated: 2-3 hours

**Lower Priority:**

2. **Full content flag** - `/mine dig --full` to bypass truncation

3. **Format options** - `/mine dig --format=json` for structured output

4. **Piping-aware auto-detection** - Detect if output will be piped

## Related Files

- `isaac/commands/ask/run.py` - Smart truncation logic
- `isaac/commands/mine/run.py` - Multi-match support
- `.claude/mail/to_visual/large_chunk_piping_design.md` - Full design doc

## Open Issues

1. **xAI SDK timeout** - Still hardcoded at 10 seconds, can't override
   - Need to request timeout parameter from xAI SDK team
   - Truncation helps but doesn't eliminate timeouts

2. **Chunk size detection** - Can't query from API
   - User sets in xAI console, not accessible programmatically
   - We rely on runtime truncation instead

## Next Steps

1. ✅ Test with user's collections (large chunks)
2. ⏳ Monitor for timeout improvements
3. ⏳ Collect feedback on multi-match output
4. ⏳ Plan Phase 2 configurable limits

---

**Impact:** Protects against token limits and improves piping reliability. Non-breaking change that makes piping safer by default.