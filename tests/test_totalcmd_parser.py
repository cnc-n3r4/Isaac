"""
Tests for TotalCommanderParser - Log file parsing
"""
import pytest
from pathlib import Path
from datetime import datetime
from isaac.integrations.totalcmd_parser import TotalCommanderParser
import tempfile


class TestTotalCommanderParser:
    """Test Total Commander log parsing."""
    
    def test_parse_copy_operation(self):
        """Test parsing copy operations."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write("2025-10-20 14:23:15 Copy: C:\\Projects\\Isaac\\backup.zip -> D:\\Backups\\2025-10-20\\\n")
            f.flush()
            log_path = Path(f.name)
        
        try:
            parser = TotalCommanderParser(log_path)
            operations = parser.parse_log(incremental=False)
            
            assert len(operations) == 1
            op = operations[0]
            assert op['operation'] == 'copy'
            assert 'Isaac' in op['source']
            assert 'Backups' in op['destination']
            assert '2025-10-20' in op['timestamp']
        finally:
            log_path.unlink()
    
    def test_parse_move_operation(self):
        """Test parsing move operations."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write("2025-10-20 14:25:03 Move: C:\\Downloads\\data.csv -> C:\\Projects\\Analysis\\raw_data\\\n")
            f.flush()
            log_path = Path(f.name)
        
        try:
            parser = TotalCommanderParser(log_path)
            operations = parser.parse_log(incremental=False)
            
            assert len(operations) == 1
            op = operations[0]
            assert op['operation'] == 'move'
            assert 'data.csv' in op['source']
        finally:
            log_path.unlink()
    
    def test_parse_delete_operation(self):
        """Test parsing delete operations."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write("2025-10-20 14:30:12 Delete: C:\\Temp\\old_stuff\\\n")
            f.flush()
            log_path = Path(f.name)
        
        try:
            parser = TotalCommanderParser(log_path)
            operations = parser.parse_log(incremental=False)
            
            assert len(operations) == 1
            op = operations[0]
            assert op['operation'] == 'delete'
            assert 'old_stuff' in op['source']
            assert op['destination'] is None
        finally:
            log_path.unlink()
    
    def test_incremental_parsing(self):
        """Test incremental parsing (only new entries)."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write("2025-10-20 14:00:00 Copy: C:\\file1.txt -> D:\\file1.txt\n")
            f.flush()
            log_path = Path(f.name)
        
        try:
            parser = TotalCommanderParser(log_path)
            
            # First parse
            ops1 = parser.parse_log(incremental=True)
            assert len(ops1) == 1
            
            # Add new line
            with open(log_path, 'a') as f:
                f.write("2025-10-20 15:00:00 Move: C:\\file2.txt -> D:\\file2.txt\n")
            
            # Second parse (incremental)
            ops2 = parser.parse_log(incremental=True)
            assert len(ops2) == 1  # Only the new line
            assert ops2[0]['source'] == 'C:\\file2.txt'
        finally:
            log_path.unlink()
    
    def test_missing_log_file(self):
        """Test handling of missing log file."""
        parser = TotalCommanderParser(Path("nonexistent.log"))
        operations = parser.parse_log()
        assert operations == []
    
    def test_malformed_lines(self):
        """Test handling of malformed log lines."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write("Invalid line format\n")
            f.write("2025-10-20 14:00:00 Copy: C:\\valid.txt -> D:\\valid.txt\n")
            f.write("Another bad line\n")
            f.flush()
            log_path = Path(f.name)
        
        try:
            parser = TotalCommanderParser(log_path)
            operations = parser.parse_log(incremental=False)
            
            # Should only parse valid line
            assert len(operations) == 1
            assert operations[0]['source'] == 'C:\\valid.txt'
        finally:
            log_path.unlink()
