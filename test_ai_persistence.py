#!/usr/bin/env python3
"""
Manual test script to verify AI query history persistence.
"""

import tempfile
import os
from pathlib import Path
from unittest.mock import patch

def test_ai_query_persistence():
    """Test that AI queries are persisted and loaded correctly."""

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Mock Path.home() to use our temp directory
        with patch('pathlib.Path.home', return_value=temp_path):
            from isaac.core.session_manager import SessionManager
            from isaac.adapters.bash_adapter import BashAdapter

            # Create session manager
            config = {'machine_id': 'TEST', 'ai_enabled': True}
            shell = BashAdapter()
            session_mgr = SessionManager(config, shell)

            # Initially should be empty
            print(f"Initial AI query count: {len(session_mgr.ai_query_history)}")
            assert len(session_mgr.ai_query_history) == 0

            # Add an AI query
            session_mgr.log_ai_query(
                query="find large files",
                translated_command="find . -size +100M",
                explanation="Search for files larger than 100MB",
                executed=True
            )

            print(f"After adding query: {len(session_mgr.ai_query_history)}")
            assert len(session_mgr.ai_query_history) == 1

            # Check the query was stored
            query = session_mgr.ai_query_history.queries[0]
            assert query['query'] == "find large files"
            assert query['command'] == "find . -size +100M"
            assert query['executed'] == True

            # Create a new session manager (simulating restart)
            session_mgr2 = SessionManager(config, shell)

            # Should load the persisted query
            print(f"After restart: {len(session_mgr2.ai_query_history)}")
            assert len(session_mgr2.ai_query_history) == 1

            # Check the loaded query
            loaded_query = session_mgr2.ai_query_history.queries[0]
            assert loaded_query['query'] == "find large files"
            assert loaded_query['command'] == "find . -size +100M"
            assert loaded_query['executed'] == True

            print("✅ AI query history persistence test PASSED!")

if __name__ == "__main__":
    test_ai_query_persistence()