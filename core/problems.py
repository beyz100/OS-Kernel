from core.sync import Mutex, ConditionVariable
from utils.logger import OSLogger

class BoundedBuffer:
    def __init__(self, capacity: int = 3):
        self.capacity = capacity
        self.buffer = []
        
        self.mutex = Mutex("BufferMutex")
        self.not_full = ConditionVariable("NotFull")
        self.not_empty = ConditionVariable("NotEmpty")

    def produce(self, pid: int, process_name: str, item: str) -> str:
        if not self.mutex.acquire(pid, process_name):
            return "need_lock"

        if len(self.buffer) >= self.capacity:
            OSLogger.log("Challenge", f"Buffer FULL! {process_name} must wait.")
            self.not_full.wait(pid, process_name)
            self.mutex.release(pid, process_name)
            return "buffer_full"

        self.buffer.append(item)
        OSLogger.log("Challenge", f"PRODUCED: {process_name} -> '{item}' (Buffer: {len(self.buffer)}/{self.capacity})")
        
        woken_pid = self.not_empty.signal()
        
        self.mutex.release(pid, process_name)
        return "ok", woken_pid

    def consume(self, pid: int, process_name: str):

        if not self.mutex.acquire(pid, process_name):
            return "need_lock", None, None

        if len(self.buffer) == 0:
            OSLogger.log("Challenge", f"Buffer EMPTY! {process_name} must wait.")
            self.not_empty.wait(pid, process_name)
            self.mutex.release(pid, process_name)
            return "buffer_empty", None, None

        item = self.buffer.pop(0)
        OSLogger.log("Challenge", f"CONSUMED: {process_name} <- '{item}' (Buffer: {len(self.buffer)}/{self.capacity})")
        
        woken_pid = self.not_full.signal()
        
        self.mutex.release(pid, process_name)
        return "ok", item, woken_pid