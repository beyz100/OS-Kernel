from core.memory import MemoryManager, PageFaultTrap
import pytest


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

    success = mem.deallocate(pid=3)
    assert success is True
    assert mem.frames.count(None) == 5


def test_address_translation():
    mem = MemoryManager(total_memory=100, page_size=10)
    
    success = mem.allocate(pid=1, memory_required=30)
    assert success is True
    
    phys_addr = mem.translate_address(pid=1, virtual_address=5)
    assert phys_addr is not None
    assert phys_addr % 10 == 5
    
    with pytest.raises(PageFaultTrap):
        mem.translate_address(pid=999, virtual_address=5)


def test_dirty_bit():
    mem = MemoryManager(total_memory=100, page_size=10)
    mem.allocate(pid=1, memory_required=20)
    
    phys_addr = mem.translate_address(pid=1, virtual_address=15)
    assert phys_addr is not None
    
    mem.mark_dirty(pid=1, virtual_address=15)
    
    page_num = 15 // 10
    assert mem.page_tables[1][page_num].dirty is True


def test_memory_stats():
    mem = MemoryManager(total_memory=100, page_size=10)
    
    stats = mem.get_memory_stats()
    assert stats["total_frames"] == 10
    assert stats["free_frames"] == 10
    
    mem.allocate(pid=1, memory_required=50)
    stats = mem.get_memory_stats()
    assert stats["used_frames"] == 5
    assert stats["free_frames"] == 5


def test_page_fault_unmapped_page():
    mem = MemoryManager(total_memory=100, page_size=10)
    mem.allocate(pid=1, memory_required=30)
    
    with pytest.raises(PageFaultTrap) as exc_info:
        mem.translate_address(pid=1, virtual_address=50)
    
    assert exc_info.value.pid == 1
    assert exc_info.value.virtual_address == 50
    assert exc_info.value.page_number == 5


def test_page_fault_invalid_page_entry():
    mem = MemoryManager(total_memory=100, page_size=10)
    mem.allocate(pid=1, memory_required=30)
    
    mem.page_tables[1][0].valid = False
    
    with pytest.raises(PageFaultTrap) as exc_info:
        mem.translate_address(pid=1, virtual_address=5)
    
    assert exc_info.value.pid == 1
    assert exc_info.value.page_number == 0


def test_page_fault_out_of_bounds():
    mem = MemoryManager(total_memory=100, page_size=10)
    mem.allocate(pid=1, memory_required=30)
    
    with pytest.raises(PageFaultTrap) as exc_info:
        mem.translate_address(pid=1, virtual_address=100)
    
    assert exc_info.value.pid == 1
    assert exc_info.value.page_number == 10
