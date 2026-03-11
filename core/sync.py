from utils.logger import OSLogger

class Mutex:
    def __init__(self, name: str):
        self.name = name
        self.locked = False
        self.owner_pid = None
        self.wait_queue = []

    def acquire(self, pid: int, process_name: str) -> bool:
        if not self.locked:
            self.locked = True
            self.owner_pid = pid
            OSLogger.log("Mutex", f"Lock '{self.name}' ACQUIRED by {process_name} (PID={pid})")
            return True
        else:
            if pid not in self.wait_queue:
                self.wait_queue.append(pid)
            OSLogger.log("Mutex", f"Lock '{self.name}' CONTENTION: {process_name} (PID={pid}) blocked, owner=PID={self.owner_pid}")
            return False

    def release(self, pid: int, process_name: str):
        if self.owner_pid != pid:
            OSLogger.log("Mutex", f"Lock '{self.name}' ERROR: PID={pid} tried to release but owner is PID={self.owner_pid}")
            return None

        OSLogger.log("Mutex", f"Lock '{self.name}' RELEASED by {process_name} (PID={pid})")

        if self.wait_queue:
            next_pid = self.wait_queue.pop(0)
            self.owner_pid = next_pid
            OSLogger.log("Mutex", f"Lock '{self.name}' granted to PID={next_pid}")
            return next_pid
        else:
            self.locked = False
            self.owner_pid = None
            return None