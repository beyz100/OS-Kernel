import time
from core.memory_pool import TinyMemoryPool
from core.memory import PageFaultTrap

def benchmark():
    metrics = {
        "total_accesses": 0,
        "hits": 0,
        "page_faults": 0,
        "total_hit_time_ns": 0,
        "total_fault_time_ns": 0,
        "avg_hit_time_ns": 0.0,
        "avg_fault_time_ns": 0.0,
        "fault_penalty_ratio": 0.0
    }
    pool = TinyMemoryPool(total_physical_memory=1024, page_size=64, max_virtual_memory=8192)
    pool.allocate(pid=1, memory_required=4096)
    
    for i in range(10000):
        addr = (i * 13) % 4096
        start = time.perf_counter_ns()
        try:
            pool.translate_address(1, addr)
            metrics["total_hit_time_ns"] += time.perf_counter_ns() - start
            metrics["hits"] += 1
        except PageFaultTrap:
            pool.handle_page_fault(1, addr, i)
            metrics["total_fault_time_ns"] += time.perf_counter_ns() - start
            metrics["page_faults"] += 1
        metrics["total_accesses"] += 1

    if metrics["hits"] > 0:
        metrics["avg_hit_time_ns"] = metrics["total_hit_time_ns"] / metrics["hits"]
    if metrics["page_faults"] > 0:
        metrics["avg_fault_time_ns"] = metrics["total_fault_time_ns"] / metrics["page_faults"]
    if metrics["avg_hit_time_ns"] > 0:
        metrics["fault_penalty_ratio"] = metrics["avg_fault_time_ns"] / metrics["avg_hit_time_ns"]
        
    for k, v in metrics.items():
        print(f"{k}: {v:.2f}")

if __name__ == "__main__":
    benchmark()
