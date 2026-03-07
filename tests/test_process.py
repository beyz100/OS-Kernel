from core.process import Process, ProcessState

def test_process_initialization():
    p1 = Process(pid=1, arrival_time=0, burst_time=5)
    
    assert p1.pid == 1
    assert p1.arrival_time == 0
    assert p1.burst_time == 5
    assert p1.remaining_time == 5
    assert p1.state == ProcessState.NEW