import math
from core.memory import MemoryManager, PageTableEntry
from utils.logger import OSLogger

class TinyMemoryPool(MemoryManager):
    def __init__(self, total_physical_memory: int = 32, page_size: int = 16, max_virtual_memory: int = 128):
        super().__init__(total_memory=total_physical_memory, page_size=page_size)
        self.max_virtual_memory = max_virtual_memory
        self.virtual_memory_used = 0

    def allocate(self, pid: int, memory_required: int, tick: int | None = None) -> bool:
        pages_needed = math.ceil(memory_required / self.page_size)
        mem_needed = pages_needed * self.page_size
        
        if self.virtual_memory_used + mem_needed > self.max_virtual_memory:
            OSLogger.log("Memory", f"OOM: PID={pid} requested {mem_needed}B, strict pool limit exceeded.", tick)
            return False
            
        self.page_tables[pid] = [PageTableEntry() for _ in range(pages_needed)]
        self.process_memory[pid] = {"pages_needed": pages_needed, "memory_required": memory_required}
        self.virtual_memory_used += mem_needed
        
        allocated = 0
        for i in range(self.total_frames):
            if self.frames[i] is None and allocated < pages_needed:
                self.frames[i] = pid
                self.page_tables[pid][allocated].frame_number = i
                self.page_tables[pid][allocated].valid = True
                allocated += 1
                if allocated == pages_needed:
                    break

        OSLogger.log("Memory", f"Pool Virtual allocate PID={pid}: {pages_needed} pages. Overcommit permitted.", tick)
        return True

    def deallocate(self, pid: int, tick: int | None = None) -> bool:
        if pid in self.process_memory:
            self.virtual_memory_used -= self.process_memory[pid]["pages_needed"] * self.page_size
        return super().deallocate(pid, tick)
