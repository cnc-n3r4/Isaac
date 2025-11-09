"""ChangeQueue for background file sync.

Stores file change events in SQLite for background processing.
This is a scaffold for Phase 0 auto-sync implementation.
"""
import sqlite3
from typing import List, Optional
import threading
import time
from dataclasses import dataclass


@dataclass
class ChangeEvent:
    """Represents a file change event."""
    path: str
    action: str  # 'modified', 'created', 'deleted'
    timestamp: float
    id: Optional[int] = None


class ChangeQueue:
    """SQLite-backed queue for file change events.

    Usage:
        cq = ChangeQueue()
        cq.enqueue('file.txt', 'modified')
        events = cq.dequeue_batch(10)
        cq.mark_processed(event_ids)
    """

    def __init__(self, db_path: str = ':memory:'):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT NOT NULL,
                    action TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    processed INTEGER DEFAULT 0
                )
            ''')
            conn.commit()

    def enqueue(self, path: str, action: str) -> Optional[int]:
        """Add a change event to the queue. Returns event ID or None."""
        timestamp = time.time()
        with sqlite3.connect(self.db_path) as conn:
            self._init_db_on_conn(conn)  # Ensure table exists
            cursor = conn.execute(
                'INSERT INTO changes (path, action, timestamp) VALUES (?, ?, ?)',
                (path, action, timestamp)
            )
            conn.commit()
            return cursor.lastrowid

    def dequeue_batch(self, limit: int = 10) -> List[ChangeEvent]:
        """Get unprocessed events, mark as processing."""
        with sqlite3.connect(self.db_path) as conn:
            self._init_db_on_conn(conn)  # Ensure table exists
            rows = conn.execute(
                'SELECT id, path, action, timestamp FROM changes WHERE processed = 0 ORDER BY timestamp LIMIT ?',
                (limit,)
            ).fetchall()

            events = [ChangeEvent(path=r[1], action=r[2], timestamp=r[3], id=r[0]) for r in rows]
            return events

    def mark_processed(self, event_ids: List[int]):
        """Mark events as processed."""
        if not event_ids:
            return
        with sqlite3.connect(self.db_path) as conn:
            self._init_db_on_conn(conn)  # Ensure table exists
            conn.execute(
                f'UPDATE changes SET processed = 1 WHERE id IN ({",".join("?" * len(event_ids))})',
                event_ids
            )
            conn.commit()

    def count_pending(self) -> int:
        """Count unprocessed events."""
        with sqlite3.connect(self.db_path) as conn:
            self._init_db_on_conn(conn)  # Ensure table exists
            return conn.execute('SELECT COUNT(*) FROM changes WHERE processed = 0').fetchone()[0]

    def clear_all(self):
        """Clear all events (for testing)."""
        with sqlite3.connect(self.db_path) as conn:
            self._init_db_on_conn(conn)  # Ensure table exists
            conn.execute('DELETE FROM changes')
            conn.commit()

    def _init_db_on_conn(self, conn):
        """Initialize database on a specific connection."""
        conn.execute('''
            CREATE TABLE IF NOT EXISTS changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp REAL NOT NULL,
                processed INTEGER DEFAULT 0
            )
        ''')
        conn.commit()


class BackgroundWorker:
    """Background processor for change queue.

    Runs a worker thread that periodically processes queued changes.
    """

    def __init__(self, queue: ChangeQueue, process_func, interval: float = 2.0):
        self.queue = queue
        self.process_func = process_func  # callable that takes List[ChangeEvent]
        self.interval = interval
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._stop.clear()
        if not self._thread.is_alive():
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=5.0)

    def _run(self):
        while not self._stop.is_set():
            try:
                events = self.queue.dequeue_batch(10)
                if events:
                    self.process_func(events)
                    self.queue.mark_processed([e.id for e in events if e.id])
            except Exception as e:
                # In production, log this
                print(f"BackgroundWorker error: {e}")
            time.sleep(self.interval)