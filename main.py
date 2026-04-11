from core.problems import BoundedBuffer
from core.file_system import FileSystem
from core.memory import MemoryManager, PageFaultTrap
from core.process import Process
from core.scheduler import FIFOScheduler
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
    
    try:
        phys_addr = mem.translate_address(pid=1, virtual_address=5)
        OSLogger.log("System", f"Virtual Address 5 -> Physical Address {phys_addr}", clock.current_tick)
    except PageFaultTrap as fault:
        OSLogger.log("System", f"TRAP: {fault}", clock.current_tick)
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
    
    try:
        phys_addr = mem.translate_address(pid=1, virtual_address=50)
        OSLogger.log("System", f"Virtual Address 50 -> Physical Address {phys_addr}", clock.current_tick)
    except PageFaultTrap as fault:
        OSLogger.log("System", f"PAGE FAULT TRAP - PID: {fault.pid}, VA: {fault.virtual_address}, Page: {fault.page_number}", clock.current_tick)
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
    
    scheduler = FIFOScheduler()
    p1 = Process(pid=1, arrival_time=0, burst_time=5)
    p2 = Process(pid=2, arrival_time=0, burst_time=5)
    
    OSLogger.log("System", "Starting Producer-Consumer interaction...", clock.current_tick)
    
    buffer.produce(process=p1, item="O2_Level=21%", scheduler=scheduler, tick=clock.current_tick)
    clock.tick()
    
    buffer.produce(process=p1, item="O2_Level=20%", scheduler=scheduler, tick=clock.current_tick)
    clock.tick()
    
    buffer.produce(process=p1, item="O2_Level=19%", scheduler=scheduler, tick=clock.current_tick)
    clock.tick()
    
    buffer.consume(process=p2, scheduler=scheduler, tick=clock.current_tick)
    clock.tick()


def run_integrated_baseline_scenario():
    print("\n" + "=" * 60)
    print("  SCENARIO 4: INTEGRATED BASELINE (SCHEDULER + MEMORY + FS + SYNC)")
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

    buffer.produce(process=p1, item="msg-1", scheduler=scheduler, tick=clock.current_tick)
    buffer.consume(process=p2, scheduler=scheduler, tick=clock.current_tick)

    for _ in range(4):
        scheduler.step(clock.current_tick)
        clock.tick()

    memory.deallocate(pid=101, tick=clock.current_tick)
    memory.deallocate(pid=102, tick=clock.current_tick)
    OSLogger.log("System", "Integrated baseline scenario completed.", clock.current_tick)


def run_cross_component_interaction():
    print("\n" + "=" * 60)
    print("  SCENARIO 5: CROSS-COMPONENT INTERACTION I (MEMORY + SCHEDULER)")
    print("=" * 60)

    clock = Clock()
    scheduler = FIFOScheduler()
    memory = MemoryManager(total_memory=64, page_size=8)
    
    p1 = Process(pid=201, arrival_time=0, burst_time=5)
    scheduler.add_process(p1, clock.current_tick)
    
    scheduler.step(clock.current_tick)
    clock.tick()
    
    memory.allocate(pid=201, memory_required=16, tick=clock.current_tick)
    
    memory.page_tables[201][0].valid = False
    memory.page_tables[201][0].frame_number = None
    
    virtual_address = 0
    OSLogger.log("Process", f"PID {p1.pid} requesting access to Virtual Address {virtual_address}", clock.current_tick)
    
    try:
        phys_addr = memory.translate_address(pid=201, virtual_address=virtual_address)
    except PageFaultTrap as e:
        OSLogger.log("Kernel", "Caught PageFaultTrap, blocking process...", clock.current_tick)
        scheduler.block_process(p1, clock.current_tick)
        
        scheduler.step(clock.current_tick)
        clock.tick()
        
        OSLogger.log("Kernel", "Fetching required page into physical memory...", clock.current_tick)
        memory.handle_page_fault(pid=e.pid, virtual_address=e.virtual_address, tick=clock.current_tick)
        clock.tick()
        
        scheduler.unblock_process(p1, clock.current_tick)
        
        scheduler.step(clock.current_tick)
        clock.tick()

        OSLogger.log("Process", f"PID {p1.pid} retrying access to Virtual Address {virtual_address}", clock.current_tick)
        phys_addr = memory.translate_address(pid=201, virtual_address=virtual_address)
        OSLogger.log("Process", f"Access SUCCESS -> Physical Address {phys_addr}", clock.current_tick)


def run_cross_component_interaction2():
    print("\n" + "=" * 60)
    print("  SCENARIO 6: CROSS-COMPONENT INTERACTION II (I/O + SCHEDULER)")
    print("=" * 60)

    clock = Clock()
    scheduler = FIFOScheduler()
    fs = FileSystem(cache_size=2)
    
    p1 = Process(pid=301, arrival_time=0, burst_time=6, name="LoggerProcess")
    p2 = Process(pid=302, arrival_time=0, burst_time=4, name="CalculatorProcess")
    
    scheduler.add_process(p1, clock.current_tick)
    scheduler.add_process(p2, clock.current_tick)
    
    # Tick 1: P1 runs
    scheduler.step(clock.current_tick)
    clock.tick()
    
    fs.create("system.log", p1.name)
    io_req = fs.request_write(p1, "system.log", "INIT")
    scheduler.handle_io_request(p1, io_req, clock.current_tick)
    
    for _ in range(8):
        scheduler.step(clock.current_tick)
        clock.tick()

if __name__ == "__main__":
    run_memory_scenario()
    run_filesystem_scenario()
    run_producer_consumer_scenario()
    run_integrated_baseline_scenario()
    run_cross_component_interaction()
    run_cross_component_interaction2()
    
    print("\n" + "="*60)
    print("  ALL SCENARIOS COMPLETED SUCCESSFULLY.")
    print("="*60 + "\n")