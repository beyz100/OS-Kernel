from core.process import Process, ProcessState
from core.sync import Mutex, ConditionVariable
from core.scheduler import FIFOScheduler

def test_mutex_acquire_and_release():

    mutex = Mutex(name="TestLock")
    
    p1 = Process(pid=1, arrival_time=0, burst_time=5)
    p2 = Process(pid=2, arrival_time=0, burst_time=5)
    
  
    success1 = mutex.acquire(p1)
    assert success1 is True
    assert mutex.owner == p1
    

    success2 = mutex.acquire(p2)
    assert success2 is False
    assert p2 in mutex.wait_queue 
    

    next_process = mutex.release(p1)
    assert next_process == p2
    assert mutex.owner == p2

def test_mutex_with_scheduler():
    scheduler = FIFOScheduler()
    mutex = Mutex("TestLock")
    p1 = Process(pid=1, arrival_time=0, burst_time=5)
    p2 = Process(pid=2, arrival_time=0, burst_time=5)
    p3 = Process(pid=3, arrival_time=0, burst_time=5)
    
    scheduler.add_process(p1, 0)
    scheduler.add_process(p2, 0)
    scheduler.add_process(p3, 0)

    # p1 acquires lock
    assert mutex.acquire(p1, scheduler, 0) is True
    
    # p2 tries and gets blocked
    assert mutex.acquire(p2, scheduler, 0) is False
    assert p2.state == ProcessState.WAITING
    assert p2 not in scheduler.ready_queue
    
    # p3 tries and gets blocked
    assert mutex.acquire(p3, scheduler, 0) is False
    assert p3.state == ProcessState.WAITING
    assert p3 not in scheduler.ready_queue

    # p1 releases lock
    next_process = mutex.release(p1, scheduler, 1)
    assert next_process == p2
    assert p2.state == ProcessState.READY
    assert p2 in scheduler.ready_queue

def test_condition_variable_with_scheduler():
    scheduler = FIFOScheduler()
    cv = ConditionVariable("TestCV")
    p1 = Process(pid=1, arrival_time=0, burst_time=5)
    p2 = Process(pid=2, arrival_time=0, burst_time=5)

    scheduler.add_process(p1, 0)
    scheduler.add_process(p2, 0)

    # p1 waits on CV
    cv.wait(p1, scheduler, 0)
    assert p1.state == ProcessState.WAITING
    assert p1 not in scheduler.ready_queue

    # p2 waits on CV
    cv.wait(p2, scheduler, 0)
    assert p2.state == ProcessState.WAITING
    assert p2 not in scheduler.ready_queue

    # Signal wakes up p1
    woken = cv.signal(scheduler, 1)
    assert woken == p1
    assert p1.state == ProcessState.READY
    assert p1 in scheduler.ready_queue
    
    # p2 is still waiting
    assert p2.state == ProcessState.WAITING