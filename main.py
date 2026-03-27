from core.problems import BoundedBuffer
from core.file_system import FileSystem
from core.memory import MemoryManager
from utils.clock import Clock
from utils.logger import OSLogger


def run_memory_scenario():
    print("\n" + "="*70)
    print("  SCENARIO 1: BASELINE PAGING MEMORY MANAGER (ADDRESS TRANSLATION)")
    print("="*70)
    
    clock = Clock()
    mem = MemoryManager(total_memory=100, page_size=10)
    
    OSLogger.log("System", "Starting memory allocation & translation tests...", clock.current_tick)
    
    success = mem.allocate(pid=1, memory_required=30)
    OSLogger.log("System", f"PID 1 Allocation: {success}", clock.current_tick)
    clock.tick()
    
    phys_addr = mem.translate_address(pid=1, virtual_address=5)
    OSLogger.log("System", f"Virtual Address 5 -> Physical Address {phys_addr}", clock.current_tick)
    clock.tick()
    
    mem.mark_dirty(pid=1, virtual_address=15)
    OSLogger.log("System", "Marked page 1 as dirty", clock.current_tick)
    clock.tick()
    
    success = mem.allocate(pid=2, memory_required=40)
    OSLogger.log("System", f"PID 2 Allocation: {success}", clock.current_tick)
    clock.tick()
    
    stats = mem.get_memory_stats()
    OSLogger.log("System", f"Memory Stats: {stats['used_frames']}/{stats['total_frames']} frames used ({stats['utilization']:.1f}%)", clock.current_tick)
    clock.tick()
    
    success = mem.deallocate(pid=1)
    OSLogger.log("System", f"PID 1 Deallocation: {success}", clock.current_tick)
    clock.tick()
    
    stats = mem.get_memory_stats()
    OSLogger.log("System", f"After dealloc: {stats['used_frames']}/{stats['total_frames']} frames used", clock.current_tick)


def run_filesystem_scenario():
    print("\n" + "="*70)
    print("  SCENARIO 2: FILE SYSTEM OPERATIONS (WITH CACHING)")
    print("="*70)
    
    clock = Clock()
    fs = FileSystem(cache_size=2)
    
    OSLogger.log("System", "Starting File System I/O tests...", clock.current_tick)
    
    success, latency = fs.create("vitals.log", "ProcessA")
    OSLogger.log("System", f"Create vitals.log: {success} (latency={latency})", clock.current_tick)
    clock.tick()
    
    success, latency = fs.write("vitals.log", "HR=80 BP=120 ", "ProcessA")
    OSLogger.log("System", f"Write vitals.log: {success} (latency={latency})", clock.current_tick)
    clock.tick()
    
    success, latency = fs.create("events.log", "ProcessB")
    OSLogger.log("System", f"Create events.log: {success} (latency={latency})", clock.current_tick)
    clock.tick()
    
    success, latency = fs.write("events.log", "START ", "ProcessB")
    OSLogger.log("System", f"Write events.log: {success} (latency={latency})", clock.current_tick)
    clock.tick()
    
    data, read_latency = fs.read("vitals.log", "ProcessC")  # CACHE MISS
    OSLogger.log("System", f"Read vitals.log: latency={read_latency} (MISS)", clock.current_tick)
    clock.tick()
    
    data, read_latency = fs.read("vitals.log", "ProcessD")  # CACHE HIT
    OSLogger.log("System", f"Read vitals.log: latency={read_latency} (HIT)", clock.current_tick)
    clock.tick()
    
    stats = fs.get_stats()
    OSLogger.log("System", f"FileSystem Stats: {stats['total_files']} files, {stats['total_size']} bytes", clock.current_tick)
    clock.tick()
    
    success = fs.delete("vitals.log", "ProcessA")
    OSLogger.log("System", f"Delete vitals.log: {success}", clock.current_tick)
    clock.tick()
    
    exists = fs.exists("vitals.log")
    OSLogger.log("System", f"vitals.log exists: {exists}", clock.current_tick)


def run_producer_consumer_scenario():
    print("\n" + "="*70)
    print("  SCENARIO 3: PRODUCER-CONSUMER (SYNCHRONIZATION)")
    print("="*70)
    
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


if __name__ == "__main__":
    run_memory_scenario()
    run_filesystem_scenario()
    run_producer_consumer_scenario()
    
    print("\n" + "="*70)
    print("  ALL SCENARIOS COMPLETED SUCCESSFULLY")
    print("="*70)
    
    print("\n" + "="*60)
    print("  ALL SCENARIOS COMPLETED SUCCESSFULLY.")
    print("="*60 + "\n")