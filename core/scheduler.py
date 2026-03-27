from collections import deque
from core.process import Process, ProcessState
from utils.logger import OSLogger

class FIFOScheduler:
    def __init__(self):
        self.ready_queue = deque() 
        self.current_process = None

    def add_process(self, process: Process, tick: int | None = None):
        process.state = ProcessState.READY
        self.ready_queue.append(process)
        OSLogger.log("Scheduler", f"Process PID={process.pid} moved to READY queue.", tick)

    def unblock_process(self, process: Process, tick: int | None = None):
        process.state = ProcessState.READY
        self.ready_queue.append(process)
        OSLogger.log("Scheduler", f"Process PID={process.pid} unblocked and re-queued.", tick)

    def step(self, tick: int | None = None):
        if self.current_process and self.current_process.state == ProcessState.BLOCKED:
            OSLogger.log("Scheduler", f"Process PID={self.current_process.pid} is BLOCKED. CPU released.", tick)
            self.current_process = None 

        if self.current_process is None or self.current_process.state == ProcessState.TERMINATED:
            if not self.ready_queue:
                OSLogger.log("Scheduler", "No READY process. CPU is idle.", tick)
                return None  
            
            self.current_process = self.ready_queue.popleft()
            self.current_process.state = ProcessState.RUNNING
            OSLogger.log("Scheduler", f"Dispatched PID={self.current_process.pid} to RUNNING.", tick)

        self.current_process.remaining_time -= 1
        OSLogger.log(
            "Scheduler",
            f"Executed PID={self.current_process.pid}, remaining={self.current_process.remaining_time}.",
            tick,
        )

        if self.current_process.remaining_time == 0:
            self.current_process.state = ProcessState.TERMINATED
            OSLogger.log("Scheduler", f"PID={self.current_process.pid} TERMINATED.", tick)

        return self.current_process