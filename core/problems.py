from core.sync import Mutex, ConditionVariable
from utils.logger import OSLogger

class BoundedBuffer:
    def __init__(self, capacity: int = 3):
        self.capacity = capacity
        self.buffer = []
        
        self.mutex = Mutex("BufferMutex")
        self.not_full = ConditionVariable("NotFull")
        self.not_empty = ConditionVariable("NotEmpty")

    def produce(self, process, item: str, scheduler=None, tick: int | None = None) -> str:
        if not self.mutex.acquire(process, scheduler, tick):
            return "need_lock"

        if len(self.buffer) >= self.capacity:
            OSLogger.log("Challenge", f"Buffer FULL! PID={process.pid} must wait.")
            self.not_full.wait(process, scheduler, tick)
            self.mutex.release(process, scheduler, tick)
            return "buffer_full"

        self.buffer.append(item)
        OSLogger.log("Challenge", f"PRODUCED: PID={process.pid} -> '{item}' (Buffer: {len(self.buffer)}/{self.capacity})")
        
        woken_process = self.not_empty.signal(scheduler, tick)
        
        self.mutex.release(process, scheduler, tick)
        return "ok"

    def consume(self, process, scheduler=None, tick: int | None = None):

        if not self.mutex.acquire(process, scheduler, tick):
            return "need_lock", None

        if len(self.buffer) == 0:
            OSLogger.log("Challenge", f"Buffer EMPTY! PID={process.pid} must wait.")
            self.not_empty.wait(process, scheduler, tick)
            self.mutex.release(process, scheduler, tick)
            return "buffer_empty", None

        item = self.buffer.pop(0)
        OSLogger.log("Challenge", f"CONSUMED: PID={process.pid} <- '{item}' (Buffer: {len(self.buffer)}/{self.capacity})")
        
        woken_process = self.not_full.signal(scheduler, tick)
        
        self.mutex.release(process, scheduler, tick)
        return "ok", item