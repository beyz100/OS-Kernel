import math
from utils.logger import OSLogger


class PageFaultTrap(Exception):
    def __init__(self, pid: int, virtual_address: int, page_number: int):
        self.pid = pid
        self.virtual_address = virtual_address
        self.page_number = page_number
        super().__init__(f"PAGE FAULT: PID={pid}, VA={virtual_address}, Page={page_number}")


class PageTableEntry:
    def __init__(self):
        self.frame_number = None
        self.valid = False
        self.dirty = False
        self.accessed = False


class MemoryManager:

    def __init__(self, total_memory: int = 1024, page_size: int = 16):
        self.total_memory = total_memory
        self.page_size = page_size
        self.total_frames = total_memory // page_size
        
        self.frames = [None] * self.total_frames

        self.replacement_pointer = 0

        self.page_tables = {}
        self.process_memory = {}

        OSLogger.log("Memory", f"Initialized: {total_memory} bytes, {self.total_frames} frames, page_size={page_size}")
    
    def allocate(self, pid: int, memory_required: int, tick: int | None = None) -> bool:
        pages_needed = math.ceil(memory_required / self.page_size)
        free_frames = self.frames.count(None)
        
        if pages_needed > free_frames:
            OSLogger.log(
                "Memory",
                f"Allocation FAILED for PID={pid}: needs {pages_needed} pages, free={free_frames}.",
                tick,
            )
            return False
        
        self.page_tables[pid] = [PageTableEntry() for _ in range(pages_needed)]
        self.process_memory[pid] = {"pages_needed": pages_needed, "memory_required": memory_required}
        
        allocated = 0
        for i in range(self.total_frames):
            if self.frames[i] is None and allocated < pages_needed:
                self.frames[i] = pid
                self.page_tables[pid][allocated].frame_number = i
                self.page_tables[pid][allocated].valid = True
                allocated += 1
                if allocated == pages_needed:
                    break

        OSLogger.log(
            "Memory",
            f"Allocated {pages_needed} page(s) to PID={pid} (free={self.frames.count(None)}).",
            tick,
        )
        return True
    
    def translate_address(self, pid: int, virtual_address: int) -> int | None:
        if pid not in self.page_tables:
            OSLogger.log("Memory", f"Translation ERROR: PID {pid} not found in page tables")
            raise PageFaultTrap(pid, virtual_address, -1)
        
        page_number = virtual_address // self.page_size
        offset = virtual_address % self.page_size
        
        if page_number >= len(self.page_tables[pid]):
            OSLogger.log("Memory", f"PAGE FAULT: Page {page_number} out of bounds for PID {pid}")
            raise PageFaultTrap(pid, virtual_address, page_number)
        
        page_entry = self.page_tables[pid][page_number]
        
        if not page_entry.valid or page_entry.frame_number is None:
            OSLogger.log("Memory", f"PAGE FAULT: PID {pid}, Virtual Address {virtual_address}")
            raise PageFaultTrap(pid, virtual_address, page_number)
        
        page_entry.accessed = True
        
        physical_address = page_entry.frame_number * self.page_size + offset
        
        return physical_address

    # ------------------------------------------------------------------
    # Clock (Second-Chance) page replacement  — Fix #2 & #4
    # ------------------------------------------------------------------
    def _find_victim_frame(self, tick: int | None = None) -> int:
        """Clock (second-chance) page replacement.

        Scans frames starting at ``replacement_pointer``.  If a page's
        *accessed* bit is set, clear it and move on (second chance).
        Otherwise the frame is chosen as victim.  Dirty pages incur an
        extra logged write-back cost.
        """
        attempts = 0
        while attempts < self.total_frames * 2:  # safety limit
            idx = self.replacement_pointer
            pid = self.frames[idx]

            if pid is not None and pid in self.page_tables:
                victim_entry = None
                for entry in self.page_tables[pid]:
                    if entry.frame_number == idx:
                        victim_entry = entry
                        break

                if victim_entry is not None and victim_entry.accessed:
                
                    victim_entry.accessed = False
                    self.replacement_pointer = (self.replacement_pointer + 1) % self.total_frames
                    attempts += 1
                    continue

               
                if victim_entry is not None and victim_entry.dirty:
                    OSLogger.log(
                        "Memory",
                        f"DIRTY PAGE write-back: Frame {idx} (PID {pid}) — extra swap cost.",
                        tick,
                    )
                return idx
            else:
                
                return idx

            self.replacement_pointer = (self.replacement_pointer + 1) % self.total_frames
            attempts += 1

     
        return self.replacement_pointer

    def handle_page_fault(self, pid: int, virtual_address: int, tick: int | None = None) -> bool:
        page_number = virtual_address // self.page_size
        if pid not in self.page_tables or page_number >= len(self.page_tables[pid]):
            return False

        page_entry = self.page_tables[pid][page_number]

        # Try to find a free frame first
        target_frame_idx = next((i for i, f in enumerate(self.frames) if f is None), None)

        if target_frame_idx is None:
            # No free frame — invoke clock algorithm to pick a victim
            target_frame_idx = self._find_victim_frame(tick)
            victim_pid = self.frames[target_frame_idx]

            if victim_pid is not None and victim_pid in self.page_tables:
                for entry in self.page_tables[victim_pid]:
                    if entry.frame_number == target_frame_idx:
                        entry.valid = False
                        entry.frame_number = None
                        entry.dirty = False
                        OSLogger.log("Memory",
                                     f"EVICTED: Frame {target_frame_idx} (PID {victim_pid}) for new page.",
                                     tick)
                        break

            self.replacement_pointer = (self.replacement_pointer + 1) % self.total_frames

        self.frames[target_frame_idx] = pid
        page_entry.frame_number = target_frame_idx
        page_entry.valid = True
        page_entry.accessed = True

        OSLogger.log("Memory",
                     f"PAGE FETCHED for PID {pid}, Virtual Address {virtual_address} -> Frame {target_frame_idx}", tick)
        return True
    
    def mark_dirty(self, pid: int, virtual_address: int):
        if pid not in self.page_tables:
            return
        
        page_number = virtual_address // self.page_size
        if page_number < len(self.page_tables[pid]):
            self.page_tables[pid][page_number].dirty = True
    
    def deallocate(self, pid: int, tick: int | None = None) -> bool:
        if pid not in self.page_tables:
            return False
        
        released = 0
        for i in range(self.total_frames):
            if self.frames[i] == pid:
                self.frames[i] = None
                released += 1
        
        del self.page_tables[pid]
        if pid in self.process_memory:
            del self.process_memory[pid]
        
        OSLogger.log(
            "Memory",
            f"Deallocated PID={pid}, released {released} frame(s) (free={self.frames.count(None)}).",
            tick,
        )
        return True
    
    def get_free_frames(self) -> int:
        return self.frames.count(None)
    
    def get_memory_stats(self) -> dict:
        used_frames = self.total_frames - self.get_free_frames()
        return {
            "total_frames": self.total_frames,
            "used_frames": used_frames,
            "free_frames": self.get_free_frames(),
            "utilization": (used_frames / self.total_frames) * 100
        }
