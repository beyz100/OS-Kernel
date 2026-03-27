from core.problems import BoundedBuffer
from core.file_system import FileSystem
from core.memory import MemoryManager
from core.process import Process
from core.scheduler import FIFOScheduler
from utils.clock import Clock
from utils.logger import OSLogger

def run_producer_consumer_scenario():
    print("\n" + "="*60)
    print("  SCENARIO 1: PRODUCER-CONSUMER (ENGINEERING CHALLENGE)")
    print("="*60)
    
    clock = Clock()
    buffer = BoundedBuffer(capacity=2)
    
    OSLogger.log("System", "Starting Producer-Consumer interaction...", clock.current_tick)
    
    buffer.produce(pid=1, process_name="Sensor_O2", item="O2_Level=21%")
    clock.tick()
    
    buffer.produce(pid=1, process_name="Sensor_O2", item="O2_Level=20%")
    clock.tick()
    
    buffer.produce(pid=1, process_name="Sensor_O2", item="O2_Level=19%")
    clock.tick()
    
    buffer.consume(pid=2, process_name="DataLogger")
    clock.tick()

def run_fs_cache_scenario():
    print("\n" + "="*60)
    print("  SCENARIO 2: FILE SYSTEM CACHING (BASELINE VS ENHANCED)")
    print("="*60)
    
    clock = Clock()
    fs = FileSystem(cache_size=2)
    
    OSLogger.log("System", "Starting File System I/O tests...", clock.current_tick)
    
    success, latency = fs.create("vitals.log", "ProcessA")
    fs.write("vitals.log", "HeartRate=80 ", "ProcessA")
    clock.tick()
    
    data, read_latency1 = fs.read("vitals.log", "ProcessB")
    clock.tick()
    
    data, read_latency2 = fs.read("vitals.log", "ProcessC")
    clock.tick()

def run_integrated_baseline_scenario():
    print("\n" + "=" * 60)
    print("  SCENARIO 3: INTEGRATED BASELINE (SCHEDULER + MEMORY + FS + SYNC)")
    print("=" * 60)

    clock = Clock()
    scheduler = FIFOScheduler()
    memory = MemoryManager(total_memory=64, page_size=8)
    fs = FileSystem(cache_size=2)
    buffer = BoundedBuffer(capacity=2)

    p1 = Process(pid=101, arrival_time=0, burst_time=2)
    p2 = Process(pid=102, arrival_time=0, burst_time=1)

    scheduler.add_process(p1, clock.current_tick)
    scheduler.add_process(p2, clock.current_tick)

    memory.allocate(pid=101, memory_required=12, tick=clock.current_tick)
    memory.allocate(pid=102, memory_required=8, tick=clock.current_tick)

    fs.create("integrated.log", "Kernel")
    fs.write("integrated.log", "BootOK ", "Kernel")
    fs.read("integrated.log", "KernelMonitor")

    buffer.produce(pid=101, process_name="P101", item="msg-1")
    buffer.consume(pid=102, process_name="P102")

    # Run scheduler ticks while logging a unified timeline.
    for _ in range(4):
        scheduler.step(clock.current_tick)
        clock.tick()

    memory.deallocate(pid=101, tick=clock.current_tick)
    memory.deallocate(pid=102, tick=clock.current_tick)
    OSLogger.log("System", "Integrated baseline scenario completed.", clock.current_tick)

if __name__ == "__main__":
    run_producer_consumer_scenario()
    run_fs_cache_scenario()
    run_integrated_baseline_scenario()
    
    print("\n" + "="*60)
    print("  ALL SCENARIOS COMPLETED SUCCESSFULLY.")
    print("="*60 + "\n")