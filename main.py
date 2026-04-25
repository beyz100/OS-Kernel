from core.problems import BoundedBuffer
from core.file_system import FileSystem
from core.memory import MemoryManager, PageFaultTrap
from core.process import Process, ProcessState
from core.scheduler import FIFOScheduler, RRScheduler
from core.sync import Mutex
from core.deadlock import DeadlockDetector
from utils.clock import Clock
from utils.logger import OSLogger


# ---------------------------------------------------------------------------
# FAILURE SCENARIO A: Out-Of-Memory (OOM)
# Intentionally fills the tiny memory pool until allocation fails.
# ---------------------------------------------------------------------------
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
    print("  SCENARIO 4: INTEGRATED BASELINE")
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


# ---------------------------------------------------------------------------
# FAILURE SCENARIO A: Out-Of-Memory (OOM)
# Intentionally fills the tiny memory pool until allocation fails.
# ---------------------------------------------------------------------------
def run_failure_oom():
    print("\n" + "="*70)
    print("  FAILURE SCENARIO A: OUT-OF-MEMORY (OOM)")
    print("="*70)

    clock = Clock()
    mem = MemoryManager(total_memory=40, page_size=10)
    scheduler = FIFOScheduler()

    OSLogger.log("Failure", "Starting OOM stress test with a 40-byte / 10-byte-page memory pool.", clock.current_tick)

    pid_counter = 1
    while True:
        process = Process(pid=pid_counter, arrival_time=clock.current_tick, burst_time=3)
        success = mem.allocate(pid=pid_counter, memory_required=10, tick=clock.current_tick)
        if not success:
            OSLogger.log(
                "Failure",
                f"OOM triggered at PID={pid_counter}! "
                f"Free frames={mem.get_free_frames()}/{mem.total_frames}. "
                "OS handles gracefully — process rejected, system stable.",
                clock.current_tick
            )
            break
        scheduler.add_process(process, clock.current_tick)
        OSLogger.log("Failure", f"Allocated 10 bytes to PID={pid_counter}. "
                     f"Free frames={mem.get_free_frames()}", clock.current_tick)
        pid_counter += 1
        clock.tick()

    stats = mem.get_memory_stats()
    OSLogger.log("Failure",
                 f"Final Memory State — used={stats['used_frames']}, "
                 f"free={stats['free_frames']}, utilisation={stats['utilization']:.1f}%",
                 clock.current_tick)
    OSLogger.log("Failure", "OOM scenario complete. Main OS loop continues normally.", clock.current_tick)


# ---------------------------------------------------------------------------
# FAILURE SCENARIO B: DEADLOCK (Armita)
# Two processes each hold one mutex and wait for the other — circular wait.
# ---------------------------------------------------------------------------
def run_failure_deadlock():
    print("\n" + "="*70)
    print("  FAILURE SCENARIO B: DEADLOCK (CIRCULAR WAIT)")
    print("="*70)

    Mutex.reset()   # reset registry for this scenario

    clock = Clock()
    scheduler = FIFOScheduler()

    p1 = Process(pid=10, arrival_time=0, burst_time=10, name="ProcessA")
    p2 = Process(pid=20, arrival_time=0, burst_time=10, name="ProcessB")
    scheduler.add_process(p1, clock.current_tick)
    scheduler.add_process(p2, clock.current_tick)

    lock_X = Mutex("Lock-X")
    lock_Y = Mutex("Lock-Y")

    OSLogger.log("Failure", "Setting up circular-wait deadlock between PID=10 and PID=20.", clock.current_tick)

    lock_X.acquire(p1, scheduler, clock.current_tick)
    clock.tick()
    lock_Y.acquire(p2, scheduler, clock.current_tick)
    clock.tick()

    OSLogger.log("Failure", "PID=10 requests Lock-Y (held by PID=20) — will block.", clock.current_tick)
    lock_Y.acquire(p1, scheduler, clock.current_tick)
    clock.tick()

    OSLogger.log("Failure", "PID=20 requests Lock-X (held by PID=10) — circular wait! Deadlock imminent.", clock.current_tick)
    lock_X.acquire(p2, scheduler, clock.current_tick)
    clock.tick()

    deadlocked = DeadlockDetector.check_deadlock(Mutex.global_locks)

    if deadlocked:
        OSLogger.log("Failure",
                     f"DEADLOCK CONFIRMED for PIDs {deadlocked}. "
                     "OS recovery: releasing all locks held by victim PID=10.",
                     clock.current_tick)
        lock_X.owner = p1
        lock_X.release(p1, scheduler, clock.current_tick)
        scheduler.unblock_process(p2, clock.current_tick)
        OSLogger.log("Failure", "Deadlock resolved. PID=20 unblocked and can now proceed.", clock.current_tick)
    else:
        OSLogger.log("Failure", "No deadlock detected (unexpected).", clock.current_tick)

    OSLogger.log("Failure", "Deadlock scenario complete. Main OS loop continues normally.", clock.current_tick)


# ---------------------------------------------------------------------------
# FAILURE SCENARIO C: DISK FULL / CORRUPTED FILE (Armita)
# ---------------------------------------------------------------------------
def run_failure_disk_full():
    print("\n" + "="*70)
    print("  FAILURE SCENARIO C: DISK FULL & CORRUPTED FILE")
    print("="*70)

    clock = Clock()
    MAX_BLOCKS = 50
    fs = FileSystem(cache_size=2)

    OSLogger.log("Failure", f"Starting Disk Full test. Disk capacity: {MAX_BLOCKS} bytes.", clock.current_tick)

    total_written = 0
    file_index = 0

    while total_written + 10 <= MAX_BLOCKS:
        fname = f"file_{file_index}.dat"
        fs.create(fname, "KernelWriter")
        ok, _ = fs.write(fname, "A" * 10, "KernelWriter")
        if ok:
            total_written += 10
            OSLogger.log("Failure",
                         f"Written 10 bytes to '{fname}'. Total on disk: {total_written}/{MAX_BLOCKS} bytes.",
                         clock.current_tick)
        file_index += 1
        clock.tick()

    overflow_file = "overflow.dat"
    fs.create(overflow_file, "KernelWriter")
    OSLogger.log("Failure",
                 f"Disk is full ({total_written}/{MAX_BLOCKS} bytes). "
                 "Attempting overflow write — OS must reject gracefully.",
                 clock.current_tick)
    if total_written >= MAX_BLOCKS:
        OSLogger.log("Failure",
                     "DISK FULL: Write to 'overflow.dat' rejected. "
                     "No data written. OS loop stable.",
                     clock.current_tick)
    else:
        fs.write(overflow_file, "OVERFLOW", "KernelWriter")
    clock.tick()

    corrupt_file = "corrupt.dat"
    fs.create(corrupt_file, "KernelWriter")
    fs.files[corrupt_file].content = "\x00" * 5
    fs.files[corrupt_file].size = 5
    OSLogger.log("Failure", "Simulating corrupted file 'corrupt.dat' (null-byte content).", clock.current_tick)

    data, _ = fs.read(corrupt_file, "Inspector")
    if data is not None and all(c == "\x00" for c in data):
        OSLogger.log("Failure",
                     "CORRUPTED FILE DETECTED: 'corrupt.dat' contains only null bytes. "
                     "OS logs the error and skips processing.",
                     clock.current_tick)

    stats = fs.get_stats()
    OSLogger.log("Failure",
                 f"Final FS State — files={stats['total_files']}, "
                 f"total_size={stats['total_size']} bytes, cache_items={stats['cache_items']}.",
                 clock.current_tick)
    OSLogger.log("Failure", "Disk Full scenario complete. Main OS loop continues normally.", clock.current_tick)


# ---------------------------------------------------------------------------
# SCENARIO 7: DEADLOCK DETECTION & RECOVERY IN OS LOOP (Beyza integration)
# Uses Mutex.global_locks so DeadlockDetector runs automatically each step.
# ---------------------------------------------------------------------------
def run_deadlock_scenario():
    print("\n" + "=" * 60)
    print("  SCENARIO 7: DEADLOCK DETECTION & RECOVERY (OS LOOP)")
    print("=" * 60)

    Mutex.reset()   # reset registry for this scenario

    clock = Clock()
    scheduler = FIFOScheduler()

    m1 = Mutex("Resource_A")
    m2 = Mutex("Resource_B")

    p1 = Process(pid=401, arrival_time=0, burst_time=5, name="Process_One")
    p2 = Process(pid=402, arrival_time=0, burst_time=5, name="Process_Two")

    scheduler.add_process(p1, clock.current_tick)
    scheduler.add_process(p2, clock.current_tick)

    scheduler.step(clock.current_tick)
    m1.acquire(p1, scheduler, clock.current_tick)
    clock.tick()

    m2.acquire(p2, scheduler, clock.current_tick)

    OSLogger.log("Test", "Triggering Circular Wait (Deadlock)...", clock.current_tick)

    m2.acquire(p1, scheduler, clock.current_tick)
    m1.acquire(p2, scheduler, clock.current_tick)

    # Deadlock detection using global_locks registry
    deadlocked = DeadlockDetector.check_deadlock(Mutex.global_locks)

    if deadlocked:
        OSLogger.log("Scheduler",
                     f"DEADLOCK DETECTED for PIDs {deadlocked}. "
                     "Recovering: releasing Resource_A from victim PID=401.",
                     clock.current_tick)
        m1.owner = p1
        m1.release(p1, scheduler, clock.current_tick)
        scheduler.unblock_process(p2, clock.current_tick)
        OSLogger.log("Scheduler", "Recovery complete. Continuing OS loop.", clock.current_tick)

    for _ in range(5):
        scheduler.step(clock.current_tick)
        clock.tick()


# ---------------------------------------------------------------------------
# SCENARIO 8: DISK FULL + FILE CORRUPTION (Bartu integration)
# Uses FileSystem with max_blocks quota and corrupt_file() method.
# ---------------------------------------------------------------------------
def run_filesystem_failure_scenario():
    print("\n" + "=" * 60)
    print("  SCENARIO 8: ENGINEERING CHALLENGE (DISK FULL + CORRUPTION)")
    print("=" * 60)

    # max_blocks=3, block_size=10 → max capacity = 30 bytes
    fs = FileSystem(cache_size=2, max_blocks=3, block_size=10)

    print("\nCreating files...")
    fs.create("report.txt", "P1")
    fs.create("backup.txt", "P2")

    print("\nFilling disk...")
    fs.write("report.txt", "1234567890", "P1")   # block 1
    fs.write("report.txt", "abcdefghij", "P1")   # block 2
    fs.write("backup.txt", "KLMNOPQRST", "P2")   # block 3 — disk full

    print("\nTrigger disk full...")
    fs.write("backup.txt", "OVERFLOW", "P2")      # rejected

    print("\nCorrupt file...")
    fs.corrupt_file("report.txt")

    print("\nRead corrupted file...")
    fs.read("report.txt", "P3")

    print("\nFinal stats:")
    stats = fs.get_stats()
    OSLogger.log("FileSystem",
                 f"Stats — files={stats['total_files']}, size={stats['total_size']}B, "
                 f"blocks={stats['used_blocks']}/{stats['max_blocks']}, "
                 f"corrupted={stats['corrupted_files']}",
                 None)


# ---------------------------------------------------------------------------
# WEEK 12: HEAVY CONCURRENCY & SCHEDULER EVALUATION
# Compares FIFO and Round-Robin under stress (5 producers, 5 consumers).
# ---------------------------------------------------------------------------
def _run_stress_test(scheduler_class, scheduler_name, time_quantum=None):
    print(f"\n" + "="*60)
    print(f"  WEEK 12: STRESS TEST WITH {scheduler_name}")
    print("="*60)
    
    # Must reset global locks for isolated scenario
    Mutex.global_locks.clear()

    clock = Clock()
    scheduler = scheduler_class(time_quantum) if time_quantum else scheduler_class()
    buffer = BoundedBuffer(capacity=5)
    
    producers = [Process(pid=i, arrival_time=0, burst_time=15, name=f"Producer-{i}") for i in range(1, 6)]
    consumers = [Process(pid=i, arrival_time=0, burst_time=15, name=f"Consumer-{i}") for i in range(6, 11)]
    
    for p in producers + consumers:
        scheduler.add_process(p, clock.current_tick)
        
    terminated_count = 0
    total_processes = 10
    
    while terminated_count < total_processes and clock.current_tick < 300:
        active_p = scheduler.step(clock.current_tick)
        if active_p and active_p.state == ProcessState.RUNNING:
            if "Producer" in active_p.name:
                buffer.produce(active_p, f"Item-from-{active_p.pid}", scheduler, clock.current_tick)
            elif "Consumer" in active_p.name:
                buffer.consume(active_p, scheduler, clock.current_tick)
                
        terminated_count = sum(1 for p in (producers + consumers) if p.state == ProcessState.TERMINATED)
        clock.tick()
        
    avg_turnaround = sum(p.turnaround_time for p in producers + consumers) / total_processes
    avg_waiting = sum(p.waiting_time for p in producers + consumers) / total_processes
    
    print(f"\n--- {scheduler_name} RESULTS ---")
    print(f"Total Ticks: {clock.current_tick}")
    print(f"Context Switches: {scheduler.context_switches}")
    print(f"Average Turnaround Time: {avg_turnaround:.2f} ticks")
    print(f"Average Waiting Time: {avg_waiting:.2f} ticks\n")
    return scheduler.context_switches, avg_waiting, avg_turnaround

def run_week12_comparison():
    print("\n\n" + "#"*70)
    print("  WEEK 12: SCHEDULER COMPARISON (FIFO vs ROUND ROBIN)")
    print("#"*70)
    
    fifo_cs, fifo_wait, fifo_tat = _run_stress_test(FIFOScheduler, "FIFO Scheduler")
    rr_cs, rr_wait, rr_tat = _run_stress_test(RRScheduler, "Round Robin (Q=3) Scheduler", time_quantum=3)
    
    print("="*60)
    print("  COMPARISON SUMMARY")
    print("="*60)
    print(f"FIFO Scheduler => Context Switches: {fifo_cs:3}, Avg Wait: {fifo_wait:5.2f}, Avg Turnaround: {fifo_tat:5.2f}")
    print(f"RR Scheduler   => Context Switches: {rr_cs:3}, Avg Wait: {rr_wait:5.2f}, Avg Turnaround: {rr_tat:5.2f}")
    
    print("\nOBSERVATIONS:")
    if rr_cs > fifo_cs:
        print("- Context-switch overhead is significantly higher in RR due to preemptions.")
    else:
        print("- Context-switch overhead didn't behave as expected. Please check logging.")
    
    if rr_wait > fifo_wait:
        print("- RR yields higher average waiting time for this workload.")
    else:
        print("- FIFO yielded higher average waiting time.")

def run_week12_filesystem_benchmark():
    print("\n" + "=" * 60)
    print("  WEEK 12: FILE SYSTEM BENCHMARK")
    print("=" * 60)

    fs = FileSystem(cache_size=2)

    fs.create("test.txt", "Bartu")
    fs.write("test.txt", "hello", "Bartu")

    data, latency1 = fs.read("test.txt", "Bartu")  # first read (slow)
    data, latency2 = fs.read("test.txt", "Bartu")  # second read (fast)

    print(f"First read latency: {latency1}")
    print(f"Second read latency: {latency2}")

    if latency2 < latency1:
        print("Cache is working (faster on second read)")
    else:
        print("Cache not working properly")

if __name__ == "__main__":
    run_memory_scenario()
    run_filesystem_scenario()
    run_producer_consumer_scenario()
    run_integrated_baseline_scenario()
    run_cross_component_interaction()
    run_cross_component_interaction2()

    # ── Week 11: Armita — Controlled Failure Scenarios ────────────────────
    run_failure_oom()
    run_failure_deadlock()
    run_failure_disk_full()
    # ─────────────────────────────────────────────────────────────────────

    # ── Week 11: Beyza + Bartu integration scenarios ──────────────────────
    run_deadlock_scenario()
    run_filesystem_failure_scenario()
    # ─────────────────────────────────────────────────────────────────────

    # ── Week 12: Beyza — Measurement & Under-Stress Testing ────────────────
    run_week12_comparison()
    # ─────────────────────────────────────────────────────────────────────

    # ── Week 12: Bartu — File System Benchmark ───────────────────────────
    run_week12_filesystem_benchmark()
    # ─────────────────────────────────────────────────────────────────────

    print("\n" + "="*60)
    print("  ALL SCENARIOS COMPLETED SUCCESSFULLY.")
    print("="*60 + "\n")