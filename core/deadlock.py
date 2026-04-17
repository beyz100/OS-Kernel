from utils.logger import OSLogger

class DeadlockDetector:
    @staticmethod
    def check_deadlock(locks: list) -> list:
        wait_for_graph = {}

        for lock in locks:
            if lock.owner is not None:
                for waiter in lock.wait_queue:
                    wait_for_graph[waiter.pid] = lock.owner.pid

        deadlocked_pids = []
        for start_node in wait_for_graph:
            visited = set()
            current = start_node
            
            while current in wait_for_graph:
                if current in visited:
                    deadlocked_pids.append(current)
                    break
                visited.add(current)
                current = wait_for_graph[current]

        if deadlocked_pids:
            unique_pids = list(set(deadlocked_pids))
            OSLogger.log("Failure", f"DEADLOCK DETECTED! Circular wait among PIDs: {unique_pids}")
            return unique_pids
            
        return []