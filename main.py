from core.problems import BoundedBuffer
from core.file_system import FileSystem
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

if __name__ == "__main__":
    run_producer_consumer_scenario()
    run_fs_cache_scenario()
    
    print("\n" + "="*60)
    print("  ALL SCENARIOS COMPLETED SUCCESSFULLY.")
    print("="*60 + "\n")