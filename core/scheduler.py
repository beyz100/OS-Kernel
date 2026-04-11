from collections import deque
from core.process import Process, ProcessState
from utils.logger import OSLogger

class FIFOScheduler:
    def __init__(self):
        self.ready_queue = deque() 
        self.current_process = None
        self.io_wait_queue = []


    def add_process(self, process: Process, tick: int | None = None):
        process.state = ProcessState.READY
        self.ready_queue.append(process)
        OSLogger.log("Scheduler", f"Process PID={process.pid} moved to READY queue.", tick)

    def block_process(self, process: Process, tick: int | None = None):
        process.state = ProcessState.WAITING
        if process in self.ready_queue:
            self.ready_queue.remove(process)
        OSLogger.log("Scheduler", f"Process PID={process.pid} blocked and moved to WAITING.", tick)

    def unblock_process(self, process: Process, tick: int | None = None):
        process.state = ProcessState.READY
        self.ready_queue.append(process)
        OSLogger.log("Scheduler", f"Process PID={process.pid} unblocked and re-queued.", tick)

    def handle_io_request(self, process: Process, io_request, tick: int | None = None):
        if io_request.should_block:
            self.block_process(process, tick)
            self.io_wait_queue.append([process, io_request.delay])
            OSLogger.log("Scheduler", f"Process PID={process.pid} blocked for {io_request.delay} ticks due to I/O.", tick)

    def step(self, tick: int | None = None):
        if self.io_wait_queue:
            completed_io = []
            for item in self.io_wait_queue:
                item[1] -= 1
                if item[1] <= 0:
                    completed_io.append(item[0])
            
            for p in completed_io:
                self.unblock_process(p, tick)
                self.io_wait_queue = [x for x in self.io_wait_queue if x[0] != p]

        if self.current_process and self.current_process.state == ProcessState.WAITING:
            OSLogger.log("Scheduler", f"Process PID={self.current_process.pid} is WAITING. CPU released.", tick)
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