"""Simple file watcher with debounce.

This is a lightweight, dependency-free watcher intended as a scaffold.
It polls file modification times and calls a callback when files change.
"""
from pathlib import Path
import threading
import time
from typing import Callable, Iterable, Dict, Optional

from .change_queue import ChangeQueue


class FileWatcher:
    """Poll-based file watcher.

    Usage:
        fw = FileWatcher(paths, callback)
        fw.start()
        fw.stop()
    """

    def __init__(self, paths: Iterable[Path], callback: Optional[Callable[[Path], None]] = None, 
                 queue: Optional[ChangeQueue] = None, poll_interval: float = 1.0, debounce: float = 1.0):
        self.paths = [Path(p) for p in paths]
        self.callback = callback
        self.queue = queue
        self.poll_interval = float(poll_interval)
        self.debounce = float(debounce)
        self._mtimes: Dict[Path, float] = {}
        self._last_called: Dict[Path, float] = {}
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        # initialize mtimes
        for p in self.paths:
            try:
                self._mtimes[p] = p.stat().st_mtime
            except Exception:
                self._mtimes[p] = 0.0
        self._stop.clear()
        if not self._thread.is_alive():
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=2.0)

    def _run(self):
        while not self._stop.is_set():
            for p in list(self.paths):
                try:
                    mtime = p.stat().st_mtime
                except Exception:
                    mtime = 0.0
                prev = self._mtimes.get(p, 0.0)
                if mtime and mtime != prev:
                    now = time.time()
                    last = self._last_called.get(p, 0.0)
                    # debounce
                    if now - last >= self.debounce:
                        try:
                            if self.callback:
                                self.callback(p)
                            if self.queue:
                                self.queue.enqueue(str(p), 'modified')
                        except Exception:
                            # callback should handle its own errors; ignore here
                            pass
                        self._last_called[p] = now
                    self._mtimes[p] = mtime
            time.sleep(self.poll_interval)


def watch(paths, callback=None, queue=None, poll_interval=1.0, debounce=1.0):
    """Convenience helper that returns a running watcher."""
    fw = FileWatcher(paths, callback=callback, queue=queue, poll_interval=poll_interval, debounce=debounce)
    fw.start()
    return fw
