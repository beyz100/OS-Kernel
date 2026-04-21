from collections import deque
from core.process import Process, ProcessState
from utils.logger import OSLogger

class FIFOScheduler:
    def __init__(self):
        self.ready_queue = deque() 
        self.current_process = None
        self.io_wait_queue = []
        self.all_processes = {}
        self.context_switches = 0


    def add_process(self, process: Process, tick: int | None = None):
        self.all_processes[process.pid] = process
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
        if process not in self.ready_queue and self.current_process != process:
            self.ready_queue.append(process)
        OSLogger.log("Scheduler", f"Process PID={process.pid} unblocked and re-queued.", tick)

    def handle_io_request(self, process: Process, io_request, tick: int | None = None):
        if io_request.should_block:
            self.block_process(process, tick)
            self.io_wait_queue.append([process, io_request.delay])
            OSLogger.log("Scheduler", f"Process PID={process.pid} blocked for {io_request.delay} ticks due to I/O.", tick)

    def terminate_process(self, pid: int, tick: int | None = None):
        process = self.all_processes.get(pid)
        if not process: return
        process.state = ProcessState.TERMINATED
        if process in self.ready_queue:
            self.ready_queue.remove(process)
        self.io_wait_queue = [x for x in self.io_wait_queue if x[0] != process]
        if self.current_process == process:
            self.current_process = None
            
        from core.sync import Mutex
        for lock in Mutex.global_locks:
            if lock.owner == process:
                lock.release(process, self, tick)
            if process in lock.wait_queue:
                lock.wait_queue.remove(process)
        OSLogger.log("Scheduler", f"Process PID={pid} forcefully TERMINATED. Locks released.", tick)

    def step(self, tick: int | None = None):
        from core.deadlock import DeadlockDetector
        from core.sync import Mutex
        
        deadlocked_pids = DeadlockDetector.check_deadlock(Mutex.global_locks)
        if deadlocked_pids:
            victim_pid = deadlocked_pids[-1]
            OSLogger.log("Deadlock", f"Resolving deadlock by terminating victim PID={victim_pid}", tick)
            self.terminate_process(victim_pid, tick)

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
            self.context_switches += 1
            OSLogger.log("Scheduler", f"Dispatched PID={self.current_process.pid} to RUNNING.", tick)

        for p in self.ready_queue:
            p.waiting_time += 1

        self.current_process.remaining_time -= 1
        OSLogger.log(
            "Scheduler",
            f"Executed PID={self.current_process.pid}, remaining={self.current_process.remaining_time}.",
            tick,
        )

        if self.current_process.remaining_time == 0:
            self.current_process.state = ProcessState.TERMINATED
            self.current_process.turnaround_time = self.current_process.burst_time + self.current_process.waiting_time
            OSLogger.log("Scheduler", f"PID={self.current_process.pid} TERMINATED. Wait: {self.current_process.waiting_time}, TAT: {self.current_process.turnaround_time}", tick)

        return self.current_process

class RRScheduler(FIFOScheduler):
    def __init__(self, time_quantum: int = 3):
        super().__init__()
        self.time_quantum = time_quantum
        self.current_quantum = 0

    def step(self, tick: int | None = None):
        from core.deadlock import DeadlockDetector
        from core.sync import Mutex
        
        deadlocked_pids = DeadlockDetector.check_deadlock(Mutex.global_locks)
        if deadlocked_pids:
            victim_pid = deadlocked_pids[-1]
            OSLogger.log("Deadlock", f"Resolving deadlock by terminating victim PID={victim_pid}", tick)
            self.terminate_process(victim_pid, tick)

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
            self.current_quantum = 0

        # Preempt if quantum expired
        if self.current_process and self.current_process.state == ProcessState.RUNNING:
            if self.current_quantum >= self.time_quantum:
                OSLogger.log("Scheduler", f"Quantum expired for PID={self.current_process.pid}. Preempting.", tick)
                # Put back to ready queue
                self.current_process.state = ProcessState.READY
                self.ready_queue.append(self.current_process)
                self.current_process = None
                self.current_quantum = 0

        if self.current_process is None or self.current_process.state == ProcessState.TERMINATED:
            if not self.ready_queue:
                OSLogger.log("Scheduler", "No READY process. CPU is idle.", tick)
                return None  
            
            self.current_process = self.ready_queue.popleft()
            self.current_process.state = ProcessState.RUNNING
            self.context_switches += 1
            self.current_quantum = 0
            OSLogger.log("Scheduler", f"Dispatched PID={self.current_process.pid} to RUNNING.", tick)

        for p in self.ready_queue:
            p.waiting_time += 1

        self.current_process.remaining_time -= 1
        self.current_quantum += 1
        
        OSLogger.log(
            "Scheduler",
            f"Executed PID={self.current_process.pid}, remaining={self.current_process.remaining_time}, quantum={self.current_quantum}/{self.time_quantum}",
            tick,
        )

        if self.current_process.remaining_time == 0:
            self.current_process.state = ProcessState.TERMINATED
            self.current_process.turnaround_time = self.current_process.burst_time + self.current_process.waiting_time
            self.current_quantum = 0
            OSLogger.log("Scheduler", f"PID={self.current_process.pid} TERMINATED. Wait: {self.current_process.waiting_time}, TAT: {self.current_process.turnaround_time}", tick)

        return self.current_process