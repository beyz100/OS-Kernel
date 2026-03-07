from core.process import Process, ProcessState
from core.scheduler import FIFOScheduler

def test_fifo_scheduler():
    scheduler = FIFOScheduler()
    

    p1 = Process(pid=1, arrival_time=0, burst_time=3)
    p2 = Process(pid=2, arrival_time=1, burst_time=2)
    

    scheduler.add_process(p1)
    scheduler.add_process(p2)
    
    assert p1.state == ProcessState.READY
    assert p2.state == ProcessState.READY
    

    active_process = scheduler.step()
    assert active_process.pid == 1
    assert p1.state == ProcessState.RUNNING
    assert p1.remaining_time == 2
    

    scheduler.step()
    scheduler.step()
    assert p1.state == ProcessState.TERMINATED
    assert p1.remaining_time == 0
    

    active_process = scheduler.step()
    assert active_process.pid == 2
    assert p2.state == ProcessState.RUNNING
    assert p2.remaining_time == 1