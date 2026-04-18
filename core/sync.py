from utils.logger import OSLogger

class Mutex:
    global_locks = []

    def __init__(self, name: str):
        self.name = name
        self.locked = False
        self.owner = None
        self.wait_queue = []
        Mutex.global_locks.append(self)

    def acquire(self, process, scheduler=None, tick: int | None = None) -> bool:
        if not self.locked:
            self.locked = True
            self.owner = process
            OSLogger.log("Mutex", f"Lock '{self.name}' ACQUIRED by PID={process.pid}")
            return True
        else:
            if process not in self.wait_queue:
                self.wait_queue.append(process)
            owner_pid = self.owner.pid if self.owner else None
            OSLogger.log("Mutex", f"Lock '{self.name}' CONTENTION: PID={process.pid} blocked, owner=PID={owner_pid}")
            if scheduler:
                scheduler.block_process(process, tick)
            return False

    def release(self, process, scheduler=None, tick: int | None = None):
        if self.owner != process:
            owner_pid = self.owner.pid if self.owner else None
            OSLogger.log("Mutex", f"Lock '{self.name}' ERROR: PID={process.pid} tried to release but owner is PID={owner_pid}")
            return None

        OSLogger.log("Mutex", f"Lock '{self.name}' RELEASED by PID={process.pid}")

        if self.wait_queue:
            next_process = self.wait_queue.pop(0)
            self.owner = next_process
            OSLogger.log("Mutex", f"Lock '{self.name}' granted to PID={next_process.pid}")
            if scheduler:
                scheduler.unblock_process(next_process, tick)
            return next_process
        else:
            self.locked = False
            self.owner = None
            return None
        
        

class ConditionVariable:
    def __init__(self, name: str):
        self.name = name
        self.wait_queue = []

    def wait(self, process, scheduler=None, tick: int | None = None):
        if process not in self.wait_queue:
            self.wait_queue.append(process)
        OSLogger.log("Sync", f"Condition '{self.name}': PID={process.pid} is waiting.")
        if scheduler:
            scheduler.block_process(process, tick)

    def signal(self, scheduler=None, tick: int | None = None):
        if self.wait_queue:
            woken_process = self.wait_queue.pop(0)
            OSLogger.log("Sync", f"Condition '{self.name}': Signaled PID={woken_process.pid} to wake up.")
            if scheduler:
                scheduler.unblock_process(woken_process, tick)
            return woken_process
        return None