from collections import deque
from core.process import Process, ProcessState

class FIFOScheduler:
    def __init__(self):
        self.ready_queue = deque() 
        self.current_process = None

    def add_process(self, process: Process):
        process.state = ProcessState.READY
        self.ready_queue.append(process)

    def step(self):
        if self.current_process is None or self.current_process.state == ProcessState.TERMINATED:
            if not self.ready_queue:
                return None  
            
            self.current_process = self.ready_queue.popleft()
            self.current_process.state = ProcessState.RUNNING

        self.current_process.remaining_time -= 1

        if self.current_process.remaining_time == 0:
            self.current_process.state = ProcessState.TERMINATED

        return self.current_process