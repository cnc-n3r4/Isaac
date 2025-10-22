"""
Total Commander log parser.
Extracts file operations from WINCMD.LOG format.
"""
import re
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class TotalCommanderParser:
    """Parse Total Commander operation logs."""
    
    def __init__(self, log_path: Path):
        """
        Initialize parser.
        
        Args:
            log_path: Path to WINCMD.LOG file
        """
        self.log_path = Path(log_path)
        self.last_parsed_position = 0  # Byte offset for incremental parsing
    
    def parse_log(self, incremental: bool = True) -> List[Dict]:
        """
        Parse Total Commander log file.
        
        Args:
            incremental: Only parse new entries since last parse
        
        Returns:
            List of operation dicts
        """
        if not self.log_path.exists():
            logger.warning(f"Log file not found: {self.log_path}")
            return []
        
        operations = []
        
        try:
            with open(self.log_path, 'r', encoding='utf-8', errors='ignore') as f:
                if incremental and self.last_parsed_position > 0:
                    # Seek to last position
                    f.seek(self.last_parsed_position)
                
                for line in f:
                    op = self._parse_line(line.strip())
                    if op:
                        operations.append(op)
                
                # Update position
                self.last_parsed_position = f.tell()
        
        except Exception as e:
            logger.error(f"Error parsing log: {e}")
        
        return operations
    
    def _parse_line(self, line: str) -> Optional[Dict]:
        """
        Parse single log line.
        
        Format: YYYY-MM-DD HH:MM:SS Operation: source -> destination
        """
        # Pattern for copy/move operations
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (Copy|Move|Delete|Rename): (.+?)( -> (.+))?$'
        match = re.match(pattern, line, re.IGNORECASE)
        
        if not match:
            return None
        
        timestamp_str, operation, source, _, destination = match.groups()
        
        try:
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
        
        return {
            "timestamp": timestamp.isoformat(),
            "operation": operation.lower(),
            "source": source.strip(),
            "destination": destination.strip() if destination else None,
            "raw_line": line
        }
    
    def get_operations_since(self, since: datetime) -> List[Dict]:
        """Get operations since specific timestamp."""
        all_ops = self.parse_log(incremental=False)
        return [
            op for op in all_ops
            if datetime.fromisoformat(op['timestamp']) >= since
        ]
