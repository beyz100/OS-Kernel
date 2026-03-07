from core.memory import MemoryManager


def test_memory_allocation():
    mem = MemoryManager(total_memory=100, page_size=10)

    success = mem.allocate(pid=1, memory_required=25)
    assert success is True
    assert mem.frames.count(1) == 3
    assert mem.frames.count(None) == 7


def test_memory_exhaustion():
    mem = MemoryManager(total_memory=50, page_size=10)

    success = mem.allocate(pid=2, memory_required=60)
    assert success is False


def test_memory_deallocation():
    mem = MemoryManager(total_memory=50, page_size=10)
    mem.allocate(pid=3, memory_required=20)

    mem.deallocate(pid=3)
    assert mem.frames.count(None) == 5