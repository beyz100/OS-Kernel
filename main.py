from core.process import Process, ProcessState
from core.scheduler import FIFOScheduler
from core.memory import MemoryManager
from core.file_system import FileSystem
from core.sync import Mutex
from utils.clock import Clock
from utils.logger import OSLogger


def run_simulation():
    clock = Clock()
    scheduler = FIFOScheduler()
    memory = MemoryManager(total_memory=100)
    fs = FileSystem()
    file_lock = Mutex("LogFileLock")

    OSLogger.log("System", "Booting OS with Concurrency & FS...", clock.current_tick)

    p1 = Process(pid=1, arrival_time=0, burst_time=4)
    p2 = Process(pid=2, arrival_time=1, burst_time=3)

    memory.allocate(p1.pid, 20)
    memory.allocate(p2.pid, 20)
    scheduler.add_process(p1)
    scheduler.add_process(p2)

    OSLogger.log("System", "Starting CPU cycle...", clock.current_tick)

    while p1.state != ProcessState.TERMINATED or p2.state != ProcessState.TERMINATED:
        clock.tick()
        active = scheduler.step()

        if active is None:
            OSLogger.log("CPU", "Idle", clock.current_tick)
            continue

        OSLogger.log(
            "CPU",
            f"Executing P{active.pid} (Remaining: {active.remaining_time})",
            clock.current_tick
        )

        if active.pid == 1 and active.remaining_time == 3:
            if file_lock.acquire(active.pid, "P1"):
                fs.create("shared_data.txt", "P1")
                fs.write("shared_data.txt", "P1_Data ", "P1")

        elif active.pid == 2 and active.remaining_time == 2:
            if file_lock.acquire(active.pid, "P2"):
                fs.write("shared_data.txt", "P2_Data ", "P2")
            else:
                OSLogger.log(
                    "Scheduler",
                    "P2 blocked waiting for lock. Removing from CPU.",
                    clock.current_tick
                )

        if active.remaining_time == 0:
            if file_lock.owner_pid == active.pid:
                unblocked_pid = file_lock.release(active.pid, f"P{active.pid}")

                if unblocked_pid == 1:
                    scheduler.unblock_process(p1)
                elif unblocked_pid == 2:
                    scheduler.unblock_process(p2)

                if unblocked_pid is not None:
                    OSLogger.log(
                        "Scheduler",
                        f"P{unblocked_pid} unblocked and added back to ready queue",
                        clock.current_tick
                    )

    OSLogger.log("System", "Simulation finished.", clock.current_tick)

    final_data = fs.read("shared_data.txt", "System")
    OSLogger.log("FileSystem", f"FINAL FILE CONTENT: '{final_data}'", clock.current_tick)


if __name__ == "__main__":
    run_simulation()