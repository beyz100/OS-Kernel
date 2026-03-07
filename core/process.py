from enum import Enum

class ProcessState(Enum):
    NEW = "NEW"            
    READY = "READY"         
    RUNNING = "RUNNING"     
    BLOCKED = "BLOCKED"     
    TERMINATED = "TERMINATED" 

class Process:
    def __init__(self, pid: int, arrival_time: int, burst_time: int):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.remaining_time = burst_time 
        self.state = ProcessState.NEW
        
        self.waiting_time = 0
        self.turnaround_time = 0

    def __str__(self):
        return f"[PID: {self.pid} | State: {self.state.name} | Remaining: {self.remaining_time}]"