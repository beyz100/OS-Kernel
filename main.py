from core.process import Process
from core.scheduler import FIFOScheduler
from core.memory import MemoryManager
from utils.clock import Clock
from utils.logger import OSLogger

def run_simulation():
   
    clock = Clock()
    scheduler = FIFOScheduler()
    memory = MemoryManager(total_memory=100, page_size=10)
    
    OSLogger.log("System", "Booting Mini OS...", clock.current_tick)
    
   
    p1 = Process(pid=1, arrival_time=0, burst_time=3)
    OSLogger.log("Process", f"Created Process P{p1.pid} requiring 3 ticks and 25KB memory", clock.current_tick)
    
  
    if memory.allocate(p1.pid, 25):
        OSLogger.log("Memory", f"Allocated memory for P{p1.pid}", clock.current_tick)
        scheduler.add_process(p1)
        OSLogger.log("Scheduler", f"P{p1.pid} added to ready queue", clock.current_tick)
    else:
        OSLogger.log("Memory", f"Failed to allocate memory for P{p1.pid} (OOM)", clock.current_tick)
        return

 
    OSLogger.log("System", "Starting CPU execution cycle...", clock.current_tick)
    while p1.remaining_time > 0:
        clock.tick() 
        active_process = scheduler.step() 
        
        if active_process:
            OSLogger.log("CPU", f"Executing P{active_process.pid} (Remaining: {active_process.remaining_time})", clock.current_tick)
        else:
            OSLogger.log("CPU", "Idle", clock.current_tick)

  
    memory.deallocate(p1.pid)
    OSLogger.log("Memory", f"Deallocated memory for P{p1.pid}", clock.current_tick)
    OSLogger.log("System", "Simulation finished gracefully.", clock.current_tick)

if __name__ == "__main__":
    run_simulation()