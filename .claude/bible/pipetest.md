Here's a comprehensive piping test suite for Collections:

---START FILE CONTENT---

Collections Piping Test Suite
Phase 1: Basic Piping (Smoke Tests)
Simple Query → Ask

/mine dig "Beatles" | /ask what albums are listed?/mine dig "Pink Floyd" | /ask summarize these songs/mine dig "jazz" | /ask how many results?
Expected: Quick responses, no timeouts, smart truncation if needed

Phase 2: Edge Cases (Stress Tests)
Large Result Sets

# Search for common terms that will return many matches/mine dig "the" | /ask count how many files contain "the"/mine dig "mp3" | /ask what are the top 5 artists?
Expected: Multi-match preview kicks in (3 results × 500 chars), truncation notice if >10k total

Empty Results

/mine dig "xyzabc123notfound" | /ask what did you find?
Expected: Graceful handling, AI explains no results found

Special Characters

/mine dig "AC/DC" | /ask list the songs/mine dig "Guns N' Roses" | /ask what albums?
Expected: Proper escaping, no parse errors

Phase 3: Complex Queries (AI Understanding)
Multi-Step Analysis

/mine dig "Beatles" | /ask what year range do these songs cover?/mine dig "classical" | /ask organize by composer/mine dig "soundtrack" | /ask which movies are represented?
Expected: AI extracts patterns from search results, provides insights

Comparative Analysis

/mine dig "rock" | /ask compare the number of albums from the 70s vs 80s/mine dig "greatest hits" | /ask which artist has the most compilations?
Expected: AI processes context, returns analytical summary

Phase 4: Chain Piping (Advanced)
Triple Pipes (if supported)

/mine dig "Beatles" | /ask extract album names | /list add beatles-albums
Expected: Results flow through pipeline, final output to list command

Phase 5: Config Tuning Tests
Test Truncation Thresholds

# Before tuning/mine dig "Madonna" | /ask summarize# Note if truncation occurs# Adjust in /config console:# - piping_threshold: 20000 (double it)# - piping_max_context: 16000 (double it)# Re-test/mine dig "Madonna" | /ask summarize
Expected: More context passed through, better AI responses (if not hitting token limits)

Test Match Count

# Default: 3 matches/mine dig "love" | /ask list all songs# Adjust in /config console:# - multi_match_count: 5# Re-test/mine dig "love" | /ask list all songs
Expected: More variety in search results

Phase 6: Performance Tests
Back-to-Back Pipes (Rapid Fire)

/mine dig "artist1" | /ask summarize/mine dig "artist2" | /ask summarize/mine dig "artist3" | /ask summarize# ... repeat 10 times
Expected: No degradation, no memory leaks, consistent response times

Timeout Monitoring

# Large collections with broad queries (likely to timeout)/mine dig "music" | /ask how many files?/mine dig "song" | /ask categorize by genre
Expected: May hit 10-second xAI timeout (can't fix), but should fail gracefully with error message

Phase 7: Real-World Scenarios
Playlist Creation

/mine dig "90s alternative" | /ask create a 20-song playlist/mine dig "workout music" | /ask suggest high-energy tracks
Expected: AI uses search results to generate recommendations

Library Organization

/mine dig "unknown artist" | /ask identify these tracks/mine dig "duplicate" | /ask find potential duplicates
Expected: AI provides organizational insights

Trivia/Discovery

/mine dig "rare" | /ask what's the oldest recording?/mine dig "live" | /ask which concerts are in the library?
Expected: AI extracts interesting patterns from metadata

Success Criteria
Test Category	Pass Condition
Basic Piping	✅ All queries return results in <10s
Edge Cases	✅ No crashes, graceful error handling
Complex Queries	✅ AI provides meaningful analysis
Config Tuning	✅ Settings changes affect behavior
Performance	✅ No degradation over 10+ queries
Timeout Handling	✅ Clear error messages when xAI times out
Known Limitations
10-second xAI timeout: Cannot be fixed, inherent to xAI SDK
20MB upload limit: Requires file chunking for large datasets
Token limits: Grok-3 has 128k context, but practical limit is ~100k tokens with response overhead
Debugging Commands

# Check collection status/mine list# View current config/config console# Test without piping (isolate issues)/mine dig "test query"/ask test question without piping# Check match count and sizes/mine dig "query" --verbose  # (if implemented)
Quick Start Test Sequence
Run these 5 tests first to validate core functionality:

Basic pipe: /mine dig "Beatles" | /ask what albums?
Large result: /mine dig "the" | /ask count results
Empty result: /mine dig "notfound123" | /ask what happened?
Special chars: /mine dig "AC/DC" | /ask list songs
Complex query: /mine dig "classical" | /ask organize by composer
If all 5 pass, your piping system is solid. Move to advanced tests.
---END FILE CONTENT---

Copy that to .claude/mail/to_test/collections_piping_test_suite.md or run through it directly. The quick start sequence at the bottom gives you the fastest validation path.