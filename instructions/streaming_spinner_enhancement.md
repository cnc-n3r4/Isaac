Streaming Spinner Enhancement
Overview
Add a rotating spinner (- \ | /) before streaming text in /ask, /summarize, and /analyze commands to provide clear visual feedback that progressive output is active.

Why This Enhancement
Basic flush=True streaming may be too subtle in fast CLI environments
Spinner gives obvious "loading" indication without changing core functionality
Improves user experience for conversational AI commands
Implementation Approach
Core Logic
Cycle through spinner characters: ['-', '\', '|', '/']
Print spinner, then chunk text, then move cursor back to overwrite spinner
Use ANSI escape codes for cursor control
Clean up spinner when streaming completes
Code Changes
run.py (and similarly for /summarize, /analyze)
Replace the chunk printing loop with:


import sysimport timedef run(session_manager, args):    # ... existing code ...        try:        xai_client = session_manager.get_xai_client()        chunk_iter = xai_client.chat_stream(query)                # Spinner characters        spinners = ['-', '\\', '|', '/']        spinner_idx = 0                for chunk in chunk_iter:            # Print spinner            sys.stdout.write(spinners[spinner_idx % len(spinners)])            sys.stdout.flush()                        # Move cursor back            sys.stdout.write('\b')            sys.stdout.flush()                        # Print chunk            sys.stdout.write(chunk)            sys.stdout.flush()                        # Update spinner            spinner_idx += 1                        # Small delay for smooth animation (optional)            time.sleep(0.05)                # Clear final spinner and add newline        sys.stdout.write(' \b')  # Space then backspace to clear        sys.stdout.write('\n')        sys.stdout.flush()            except Exception as e:        print(f"Error: {str(e)}")
Key Technical Details
Use sys.stdout for direct control over output stream
\b (backspace) to overwrite spinner position
flush() after each write to ensure immediate display
Optional small delay (0.05s) for smooth rotation
Final cleanup removes spinner before newline
Dependencies
sys and time modules (already available)
No external libraries needed
Works in most modern terminals supporting ANSI codes
Testing
Test with long queries to see spinner rotation
Verify spinner disappears cleanly at end
Check behavior with short responses (spinner may not appear)
Ensure no interference with text selection/copy
Fallback
If ANSI codes don't work in some terminals, spinner can be disabled or simplified to just the flush approach.

Complexity
Medium - Cursor control requires careful sequencing but logic is straightforward.

Priority
Medium - Nice UX enhancement after core streaming is confirmed working.