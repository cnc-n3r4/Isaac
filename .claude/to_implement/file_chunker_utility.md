# File Chunker Utility for Large Collections

## Problem Statement
xAI Collections API has a **20MB gRPC message size limit**. Large files (like 44MB music library listings) fail with `RESOURCE_EXHAUSTED` error when attempting to cast.

## Real-World Use Case
- User attempted to cast 44.6MB music directory listing
- Error: `Sent message larger than max (44694775 vs. 20971520)`
- Manual workaround: Split file with PowerShell script
- **Future need**: Bot automation will require programmatic chunking

## Proposed Solution
Build `/mine chunk <file> [--max-size MB]` utility to auto-split large files before casting.

### Features
- **Auto-detection**: Check file size before upload, warn if >18MB
- **Smart chunking**: Split by lines/logical boundaries (not mid-record)
- **Batch casting**: Optionally auto-cast all chunks after splitting
- **Naming convention**: `basename_part1.txt`, `basename_part2.txt`, etc.
- **Progress feedback**: Show chunk creation progress

### Command Design
```bash
# Manual chunking
/mine chunk myMusic.txt --max-size 18
# Output: Created myMusic_part1.txt (18.0 MB), myMusic_part2.txt (18.0 MB), myMusic_part3.txt (8.6 MB)

# Chunk + auto-cast
/mine chunk myMusic.txt --max-size 18 --cast
# Chunks files, then automatically: /mine cast myMusic_part1.txt ... etc.

# Check if file needs chunking (dry run)
/mine chunk myMusic.txt --check
# Output: File is 44.6 MB, requires 3 chunks at 18 MB limit
```

### Implementation Notes
- Default max size: **18MB** (buffer below 20MB limit)
- Use byte-accurate measurement (UTF-8 encoding)
- Handle edge cases: empty files, single-line files, binary files
- Integration point: `isaac/commands/mine/run.py` (new `_handle_chunk` function)
- Consider chunking logic in `/mine cast` automatically (prompt user if >18MB detected)

### Bot Integration
When building automation bots:
- Large dataset uploads will need automatic chunking
- Bot should detect file size and chunk transparently
- User shouldn't need to manually split files

## Priority
**MEDIUM** - Not blocking current workflow, but required for:
1. Future bot automation
2. Better UX for large file uploads
3. Preventing cryptic gRPC errors

## Dependencies
- File size detection (os.path.getsize)
- Line-by-line chunking logic
- Progress indicators (optional: tqdm or manual counter)

## Acceptance Criteria
- [ ] `/mine chunk` command implemented
- [ ] Respects 18MB default limit (configurable)
- [ ] Creates numbered chunk files
- [ ] Optional `--cast` flag for batch upload
- [ ] Dry-run `--check` mode
- [ ] Error handling for I/O failures
- [ ] Unit tests for chunking logic

## Related Issues
- 20MB xAI Collections upload limit (hardcoded in gRPC)
- Music library test case (44.6MB file)

---

**Future Enhancement**: Consider adding chunk logic directly to `/mine cast` so it transparently handles large files without user intervention.