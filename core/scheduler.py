from collections import deque

from core.process import Process, ProcessState
from core.sync import Mutex                       # Fix #11: top-level import
from core.deadlock import DeadlockDetector        # Fix #11: top-level import
from utils.logger import OSLogger


class FIFOScheduler:
    """First-In-First-Out (non-preemptive) scheduler.

    The ``step()`` method is decomposed into hook methods so that
    ``RRScheduler`` can override only the parts that differ (preemption,
    dispatch reset, execute logging) instead of duplicating the entire
    method.  — Fix #12: Template Method pattern.
    """

    def __init__(self):
        self.ready_queue = deque()
        self.current_process = None
        self.io_wait_queue = []
        self.all_processes = {}
        self.context_switches = 0

    # ------------------------------------------------------------------ queue ops
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
        if not process:
            return
        process.state = ProcessState.TERMINATED
        if process in self.ready_queue:
            self.ready_queue.remove(process)
        self.io_wait_queue = [x for x in self.io_wait_queue if x[0] != process]
        if self.current_process == process:
            self.current_process = None

        for lock in list(Mutex.global_locks):  # Fix #17: iterate over copy for safety
            if lock.owner == process:
                lock.release(process, self, tick)
            if process in lock.wait_queue:
                lock.wait_queue.remove(process)
        OSLogger.log("Scheduler", f"Process PID={pid} forcefully TERMINATED. Locks released.", tick)

    # ================================================================== step()
    def step(self, tick: int | None = None):
        """Single scheduler tick — Template Method.

        Calls hook methods that subclasses can override to change
        specific behaviour (preemption, dispatch, execute).
        """
        self._run_deadlock_check(tick)
        self._tick_io(tick)
        self._release_waiting_cpu(tick)

        if self._should_preempt():
            self._preempt(tick)

        if self.current_process is None or self.current_process.state == ProcessState.TERMINATED:
            if not self.ready_queue:
                OSLogger.log("Scheduler", "No READY process. CPU is idle.", tick)
                return None
            self._dispatch(tick)

        self._tick_waiting_times()
        self._execute_tick(tick)
        self._check_termination(tick)
        return self.current_process

    # ------------------------------------------------------------------ hooks
    def _should_preempt(self) -> bool:
        """Override in preemptive schedulers."""
        return False

    def _preempt(self, tick: int | None = None):
        """Override to implement preemption logic."""
        pass

    def _dispatch(self, tick: int | None = None):
        """Pick the next process from the ready queue."""
        self.current_process = self.ready_queue.popleft()
        self.current_process.state = ProcessState.RUNNING
        self.context_switches += 1
        OSLogger.log("Scheduler", f"Dispatched PID={self.current_process.pid} to RUNNING.", tick)

    def _execute_tick(self, tick: int | None = None):
        """Consume one CPU tick for the running process."""
        self.current_process.remaining_time -= 1
        OSLogger.log(
            "Scheduler",
            f"Executed PID={self.current_process.pid}, remaining={self.current_process.remaining_time}.",
            tick,
        )

    def _check_termination(self, tick: int | None = None):
        """Check if the running process has finished."""
        if self.current_process.remaining_time == 0:
            self.current_process.state = ProcessState.TERMINATED
            self.current_process.turnaround_time = (
                self.current_process.burst_time + self.current_process.waiting_time
            )
            OSLogger.log(
                "Scheduler",
                f"PID={self.current_process.pid} TERMINATED. "
                f"Wait: {self.current_process.waiting_time}, "
                f"TAT: {self.current_process.turnaround_time}",
                tick,
            )

    # ------------------------------------------------------------------ shared helpers
    def _run_deadlock_check(self, tick: int | None = None):
        deadlocked_pids = DeadlockDetector.check_deadlock(Mutex.global_locks)
        if deadlocked_pids:
            victim_pid = deadlocked_pids[-1]
            OSLogger.log("Deadlock", f"Resolving deadlock by terminating victim PID={victim_pid}", tick)
            self.terminate_process(victim_pid, tick)

    def _tick_io(self, tick: int | None = None):
        """Decrement I/O wait counters; unblock completed processes.

        Fix #13: completed set avoids per-process list rebuild.
        """
        if not self.io_wait_queue:
            return
        completed = set()
        for item in self.io_wait_queue:
            item[1] -= 1
            if item[1] <= 0:
                completed.add(item[0])
        for p in completed:
            self.unblock_process(p, tick)
        # Single rebuild instead of one per completed process
        self.io_wait_queue = [x for x in self.io_wait_queue if x[0] not in completed]

    def _release_waiting_cpu(self, tick: int | None = None):
        """Release the CPU if the current process is blocked."""
        if self.current_process and self.current_process.state == ProcessState.WAITING:
            OSLogger.log("Scheduler", f"Process PID={self.current_process.pid} is WAITING. CPU released.", tick)
            self.current_process = None

    def _tick_waiting_times(self):
        """Increment waiting time for every process sitting in the ready queue."""
        for p in self.ready_queue:
            p.waiting_time += 1


class RRScheduler(FIFOScheduler):
    """Round-Robin scheduler — extends FIFO with quantum-based preemption.

    Only overrides the hooks that differ: preemption check, preempt action,
    dispatch reset, execute logging, and waiting-CPU release (to reset quantum).
    """

    def __init__(self, time_quantum: int = 3):
        super().__init__()
        self.time_quantum = time_quantum
        self.current_quantum = 0

    def _should_preempt(self) -> bool:
        return (
            self.current_process is not None
            and self.current_process.state == ProcessState.RUNNING
            and self.current_quantum >= self.time_quantum
        )

    def _preempt(self, tick: int | None = None):
        OSLogger.log("Scheduler", f"Quantum expired for PID={self.current_process.pid}. Preempting.", tick)
        self.current_process.state = ProcessState.READY
        self.ready_queue.append(self.current_process)
        self.current_process = None
        self.current_quantum = 0

    def _dispatch(self, tick: int | None = None):
        super()._dispatch(tick)
        self.current_quantum = 0

    def _execute_tick(self, tick: int | None = None):
        self.current_process.remaining_time -= 1
        self.current_quantum += 1
        OSLogger.log(
            "Scheduler",
            f"Executed PID={self.current_process.pid}, "
            f"remaining={self.current_process.remaining_time}, "
            f"quantum={self.current_quantum}/{self.time_quantum}",
            tick,
        )

    def _check_termination(self, tick: int | None = None):
        if self.current_process.remaining_time == 0:
            self.current_process.state = ProcessState.TERMINATED
            self.current_process.turnaround_time = (
                self.current_process.burst_time + self.current_process.waiting_time
            )
            self.current_quantum = 0
            OSLogger.log(
                "Scheduler",
                f"PID={self.current_process.pid} TERMINATED. "
                f"Wait: {self.current_process.waiting_time}, "
                f"TAT: {self.current_process.turnaround_time}",
                tick,
            )

    def _release_waiting_cpu(self, tick: int | None = None):
        if self.current_process and self.current_process.state == ProcessState.WAITING:
            OSLogger.log("Scheduler", f"Process PID={self.current_process.pid} is WAITING. CPU released.", tick)
            self.current_process = None
            self.current_quantum = 0