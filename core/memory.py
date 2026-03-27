from utils.logger import OSLogger


class MemoryManager:
    def __init__(self, total_memory: int = 1024, page_size: int = 16):
        self.total_memory = total_memory
        self.page_size = page_size
        self.total_frames = total_memory // page_size

        self.frames = [None] * self.total_frames

    def allocate(self, pid: int, memory_required: int, tick: int | None = None) -> bool:
        import math
        pages_needed = math.ceil(memory_required / self.page_size)

        free_frames = self.frames.count(None)

        if pages_needed > free_frames:
            OSLogger.log(
                "Memory",
                f"Allocation FAILED for PID={pid}: needs {pages_needed} pages, free={free_frames}.",
                tick,
            )
            return False
        allocated = 0
        for i in range(self.total_frames):
            if self.frames[i] is None:
                self.frames[i] = pid
                allocated += 1
                if allocated == pages_needed:
                    break

        OSLogger.log(
            "Memory",
            f"Allocated {pages_needed} page(s) to PID={pid} (free={self.frames.count(None)}).",
            tick,
        )
        return True

    def deallocate(self, pid: int, tick: int | None = None):
        released = 0
        for i in range(self.total_frames):
            if self.frames[i] == pid:
                self.frames[i] = None
                released += 1
        OSLogger.log(
            "Memory",
            f"Deallocated PID={pid}, released {released} frame(s) (free={self.frames.count(None)}).",
            tick,
        )