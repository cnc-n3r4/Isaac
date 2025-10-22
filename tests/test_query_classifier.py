"""
Tests for QueryClassifier - Intent classification for AI queries
"""
import pytest
from isaac.ai.query_classifier import QueryClassifier


class TestQueryClassifier:
    """Test query classification logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = QueryClassifier()
    
    def test_classify_geographic(self):
        """Test geographic query classification."""
        assert self.classifier.classify("where is alaska?") == "geographic"
        assert self.classifier.classify("capital of france") == "geographic"
        assert self.classifier.classify("location of tokyo") == "geographic"
        assert self.classifier.classify("what country is paris in") == "geographic"
    
    def test_classify_file_lookup(self):
        """Test file lookup query classification."""
        assert self.classifier.classify("where is alaska.exe?") == "file_lookup"
        assert self.classifier.classify("find notepad.exe") == "file_lookup"
        assert self.classifier.classify("locate python.py") == "file_lookup"
        assert self.classifier.classify("where is config.json") == "file_lookup"
    
    def test_classify_shell_command(self):
        """Test shell command query classification."""
        assert self.classifier.classify("list files") == "shell_command"
        assert self.classifier.classify("show processes") == "shell_command"
        assert self.classifier.classify("delete old logs") == "shell_command"
        assert self.classifier.classify("copy files to backup") == "shell_command"
    
    def test_classify_general_info(self):
        """Test general information query classification."""
        assert self.classifier.classify("what is docker?") == "general_info"
        assert self.classifier.classify("explain kubernetes") == "general_info"
        assert self.classifier.classify("how does git work") == "general_info"
        assert self.classifier.classify("tell me about python") == "general_info"
    
    def test_path_detection(self):
        """Test path-like pattern detection."""
        # Windows paths
        assert self.classifier._looks_like_path("C:\\Users\\test\\file.txt")
        assert self.classifier._looks_like_path("D:\\Projects\\isaac")
        
        # Unix paths
        assert self.classifier._looks_like_path("/usr/bin/python")
        assert self.classifier._looks_like_path("~/Documents/file.txt")
        
        # Not paths
        assert not self.classifier._looks_like_path("simple text")
        assert not self.classifier._looks_like_path("no slashes here")
    
    def test_edge_cases(self):
        """Test edge cases and ambiguous queries."""
        # "alaska" vs "alaska.exe"
        assert self.classifier.classify("where is alaska") == "geographic"
        assert self.classifier.classify("where is alaska.exe") == "file_lookup"
        
        # Command with info keyword
        assert self.classifier.classify("what files are in this directory") == "shell_command"
        
        # Empty/minimal input
        assert self.classifier.classify("") == "shell_command"
        assert self.classifier.classify("ls") == "shell_command"
    
    def test_is_chat_mode_query(self):
        """Test chat mode determination."""
        # Should be chat mode
        assert self.classifier.is_chat_mode_query("where is alaska?") == True
        assert self.classifier.is_chat_mode_query("what is docker?") == True
        
        # Should NOT be chat mode (translation mode)
        assert self.classifier.is_chat_mode_query("where is alaska.exe") == False
        assert self.classifier.is_chat_mode_query("list files") == False
