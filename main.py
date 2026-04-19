from core.problems import BoundedBuffer
from core.file_system import FileSystem
from core.memory import MemoryManager, PageFaultTrap
from core.process import Process
from core.scheduler import FIFOScheduler
from core.sync import Mutex
from core.deadlock import DeadlockDetector
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

# ---------------------------------------------------------------------------
# FAILURE SCENARIO A: Out-Of-Memory (OOM)
# Intentionally fills the tiny memory pool until allocation fails.
# ---------------------------------------------------------------------------
def run_failure_oom():
    print("\n" + "="*70)
    print("  FAILURE SCENARIO A: OUT-OF-MEMORY (OOM)")
    print("="*70)

    clock = Clock()
    # Tiny pool: only 4 frames (40 bytes / 10 per frame)
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
# FAILURE SCENARIO B: DEADLOCK
# Two processes each hold one mutex and wait for the other — circular wait.
# DeadlockDetector identifies the cycle; the OS logs & performs recovery.
# ---------------------------------------------------------------------------
def run_failure_deadlock():
    print("\n" + "="*70)
    print("  FAILURE SCENARIO B: DEADLOCK (CIRCULAR WAIT)")
    print("="*70)

    clock = Clock()
    scheduler = FIFOScheduler()

    p1 = Process(pid=10, arrival_time=0, burst_time=10, name="ProcessA")
    p2 = Process(pid=20, arrival_time=0, burst_time=10, name="ProcessB")
    scheduler.add_process(p1, clock.current_tick)
    scheduler.add_process(p2, clock.current_tick)

    lock_X = Mutex("Lock-X")
    lock_Y = Mutex("Lock-Y")

    OSLogger.log("Failure", "Setting up circular-wait deadlock between PID=10 and PID=20.", clock.current_tick)

    # P1 acquires Lock-X, P2 acquires Lock-Y
    lock_X.acquire(p1, scheduler, clock.current_tick)
    clock.tick()
    lock_Y.acquire(p2, scheduler, clock.current_tick)
    clock.tick()

    # P1 now waits for Lock-Y (held by P2) → blocked
    OSLogger.log("Failure", "PID=10 requests Lock-Y (held by PID=20) — will block.", clock.current_tick)
    lock_Y.acquire(p1, scheduler, clock.current_tick)
    clock.tick()

    # P2 now waits for Lock-X (held by P1) → blocked, circular wait established
    OSLogger.log("Failure", "PID=20 requests Lock-X (held by PID=10) — circular wait! Deadlock imminent.", clock.current_tick)
    lock_X.acquire(p2, scheduler, clock.current_tick)
    clock.tick()

    # ----------------------------------------------------------------
    # Build adapters for DeadlockDetector.check_deadlock(), which
    # expects lock.owner_pid (int|None) and lock.wait_queue of PIDs.
    # Mutex stores Process objects, so we adapt without touching
    # Beyza's detector code.
    # ----------------------------------------------------------------
    class _LockView:
        """Read-only view of a Mutex compatible with DeadlockDetector."""
        def __init__(self, mutex: Mutex):
            self.owner_pid = mutex.owner.pid if mutex.owner is not None else None
            self.wait_queue = [p.pid for p in mutex.wait_queue]

    # Run deadlock detection
    deadlocked = DeadlockDetector.check_deadlock([_LockView(lock_X), _LockView(lock_Y)])

    if deadlocked:
        OSLogger.log("Failure",
                     f"DEADLOCK CONFIRMED for PIDs {deadlocked}. "
                     "OS recovery: releasing all locks held by victim PID=10.",
                     clock.current_tick)
        # Recovery: forcibly release the victim's lock so the other can proceed
        victim = p1
        lock_X.owner = victim          # ensure owner is set for proper release
        lock_X.release(victim, scheduler, clock.current_tick)
        scheduler.unblock_process(p2, clock.current_tick)
        OSLogger.log("Failure",
                     "Deadlock resolved. PID=20 unblocked and can now proceed.",
                     clock.current_tick)
    else:
        OSLogger.log("Failure", "No deadlock detected (unexpected).", clock.current_tick)

    OSLogger.log("Failure", "Deadlock scenario complete. Main OS loop continues normally.", clock.current_tick)


# ---------------------------------------------------------------------------
# FAILURE SCENARIO C: DISK FULL / CORRUPTED FILE
# Fills the file system to its block limit, then attempts further writes &
# a corrupted-read, verifying the OS handles both gracefully.
# ---------------------------------------------------------------------------
def run_failure_disk_full():
    print("\n" + "="*70)
    print("  FAILURE SCENARIO C: DISK FULL & CORRUPTED FILE")
    print("="*70)

    clock = Clock()
    # Simulate a very small disk: cap at MAX_BLOCKS total data bytes
    MAX_BLOCKS = 50  # bytes
    fs = FileSystem(cache_size=2)

    OSLogger.log("Failure", f"Starting Disk Full test. Disk capacity: {MAX_BLOCKS} bytes.", clock.current_tick)

    total_written = 0
    file_index = 0

    # Fill the disk until adding more data would exceed capacity
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

    # Now attempt one more write that would exceed capacity
    overflow_file = "overflow.dat"
    fs.create(overflow_file, "KernelWriter")
    OSLogger.log(
        "Failure",
        f"Disk is full ({total_written}/{MAX_BLOCKS} bytes). "
        "Attempting overflow write — OS must reject gracefully.",
        clock.current_tick
    )
    # We flag the disk-full condition manually (the FS has no hard quota),
    # so we gate the write and log the failure ourselves — mirroring a real kernel check.
    disk_full = (total_written >= MAX_BLOCKS)
    if disk_full:
        OSLogger.log("Failure",
                     "DISK FULL: Write to 'overflow.dat' rejected. "
                     "No data written. OS loop stable.",
                     clock.current_tick)
    else:
        fs.write(overflow_file, "OVERFLOW", "KernelWriter")

    clock.tick()

    # Simulate a corrupted-file read: file exists but content is empty/garbled
    corrupt_file = "corrupt.dat"
    fs.create(corrupt_file, "KernelWriter")
    # Intentionally corrupt: write nothing, then manually zero out the stored content
    fs.files[corrupt_file].content = "\x00" * 5  # null bytes = corrupted
    fs.files[corrupt_file].size = 5
    OSLogger.log("Failure", "Simulating corrupted file 'corrupt.dat' (null-byte content).", clock.current_tick)

    data, _ = fs.read(corrupt_file, "Inspector")
    if data is not None and all(c == "\x00" for c in data):
        OSLogger.log("Failure",
                     "CORRUPTED FILE DETECTED: 'corrupt.dat' contains only null bytes. "
                     "OS logs the error and skips processing.",
                     clock.current_tick)
    else:
        OSLogger.log("Failure", f"Read from 'corrupt.dat': '{data}'", clock.current_tick)

    stats = fs.get_stats()
    OSLogger.log("Failure",
                 f"Final FS State — files={stats['total_files']}, "
                 f"total_size={stats['total_size']} bytes, cache_items={stats['cache_items']}.",
                 clock.current_tick)
    OSLogger.log("Failure", "Disk Full scenario complete. Main OS loop continues normally.", clock.current_tick)


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

    print("\n" + "="*60)
    print("  ALL SCENARIOS COMPLETED SUCCESSFULLY.")
    print("="*60 + "\n")