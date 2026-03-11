from core.process import Process, ProcessState
from core.sync import Mutex

def test_mutex_acquire_and_release():

    mutex = Mutex(name="TestLock")
    
    p1 = Process(pid=1, arrival_time=0, burst_time=5)
    p2 = Process(pid=2, arrival_time=0, burst_time=5)
    
  
    success1 = mutex.acquire(p1.pid, "P1")
    assert success1 is True
    assert mutex.owner_pid == 1
    

    success2 = mutex.acquire(p2.pid, "P2")
    assert success2 is False
    assert p2.pid in mutex.wait_queue 
    

    next_pid = mutex.release(p1.pid, "P1")
    assert next_pid == 2
    assert mutex.owner_pid == 2