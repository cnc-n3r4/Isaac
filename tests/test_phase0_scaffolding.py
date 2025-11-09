import time
from pathlib import Path

from isaac.core.file_watcher import FileWatcher
from isaac.core.unified_fs import UnifiedFileSystem
from isaac.core.change_queue import ChangeQueue, BackgroundWorker
from isaac.collections.git_sync import GitSync
from isaac.ai.context_gatherer import ContextGatherer


def test_unified_fs_write_read(tmp_path):
    ufs = UnifiedFileSystem()
    p = tmp_path / 'sub' / 'f.txt'
    ufs.write(str(p), 'hello')
    assert ufs.exists(str(p))
    assert ufs.read(str(p)) == 'hello'


def test_file_watcher_triggers(tmp_path):
    events = []

    def cb(path):
        events.append(str(path))

    f = tmp_path / 'watch.txt'
    f.write_text('a')
    fw = FileWatcher([f], cb, poll_interval=0.1, debounce=0.05)
    fw.start()
    try:
        # modify file
        time.sleep(0.15)
        f.write_text('b')
        # give watcher time to pick up
        time.sleep(0.3)
    finally:
        fw.stop()

    assert any('watch.txt' in e for e in events)


def test_change_queue(tmp_path):
    db_path = str(tmp_path / 'test.db')
    cq = ChangeQueue(db_path)
    # Test enqueue
    id1 = cq.enqueue('file1.txt', 'modified')
    id2 = cq.enqueue('file2.txt', 'created')
    assert id1 is not None
    assert id2 is not None
    assert id1 != id2

    # Test dequeue
    events = cq.dequeue_batch(10)
    assert len(events) == 2
    assert events[0].path == 'file1.txt'
    assert events[0].action == 'modified'
    assert events[1].path == 'file2.txt'
    assert events[1].action == 'created'

    # Test mark processed
    event_ids = [e.id for e in events if e.id is not None]
    cq.mark_processed(event_ids)
    assert cq.count_pending() == 0


def test_background_worker(tmp_path):
    db_path = str(tmp_path / 'worker.db')
    cq = ChangeQueue(db_path)
    processed = []

    def process_func(events):
        processed.extend([e.path for e in events])

    worker = BackgroundWorker(cq, process_func, interval=0.1)
    worker.start()

    try:
        # Add events
        cq.enqueue('test1.txt', 'modified')
        cq.enqueue('test2.txt', 'created')

        # Wait for processing
        time.sleep(0.5)

        assert 'test1.txt' in processed
        assert 'test2.txt' in processed
    finally:
        worker.stop()


def test_watcher_with_queue(tmp_path):
    db_path = str(tmp_path / 'watcher.db')
    cq = ChangeQueue(db_path)
    f = tmp_path / 'watch_queue.txt'
    f.write_text('initial')

    fw = FileWatcher([f], queue=cq, poll_interval=0.1, debounce=0.05)
    fw.start()

    try:
        # Modify file
        time.sleep(0.15)
        f.write_text('modified')

        # Wait for watcher
        time.sleep(0.3)

        events = cq.dequeue_batch(10)
        assert len(events) >= 1
        assert any(e.path.endswith('watch_queue.txt') and e.action == 'modified' for e in events)
    finally:
        fw.stop()


def test_git_sync_basic():
    gs = GitSync(Path('.'))
    # repo may not exist in test env; ensure methods don't crash
    _ = gs.repo_root()
    _ = gs.current_branch()
    _ = gs.diff_files()


def test_context_gatherer(tmp_path):
    cg = ContextGatherer(workspace=tmp_path)
    # create files
    for i in range(3):
        (tmp_path / f'f{i}.txt').write_text('x')
    files = cg.gather_file_list(limit=5)
    assert len(files) >= 3
    info = cg.gather_git_info()
    assert 'diff' in info and 'branch' in info
