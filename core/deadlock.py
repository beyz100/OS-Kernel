from utils.logger import OSLogger

class DeadlockDetector:
    @staticmethod
    def check_deadlock(locks: list) -> list:
        """Build a wait-for graph and detect cycles via DFS.

        Each process that is waiting for a lock adds an edge
        waiter_pid → owner_pid.  A process may wait on multiple
        locks, so the graph is dict[int, list[int]].
        """
        # Build adjacency list: waiter_pid → [owner_pids...]
        wait_for_graph: dict[int, list[int]] = {}

        for lock in locks:
            if lock.owner is not None:
                for waiter in lock.wait_queue:
                    wait_for_graph.setdefault(waiter.pid, []).append(lock.owner.pid)

        # DFS cycle detection
        deadlocked_pids: set[int] = set()

        def dfs(node: int, path: list[int], visited: set[int]) -> None:
            if node in path:
                # Cycle found — all nodes from cycle start onward are deadlocked
                cycle_start = path.index(node)
                deadlocked_pids.update(path[cycle_start:])
                return
            if node in visited or node not in wait_for_graph:
                return
            path.append(node)
            for neighbour in wait_for_graph[node]:
                dfs(neighbour, path, visited)
            path.pop()
            visited.add(node)

        visited: set[int] = set()
        for node in wait_for_graph:
            if node not in visited:
                dfs(node, [], visited)

        if deadlocked_pids:
            unique_pids = sorted(deadlocked_pids)
            OSLogger.log("Failure", f"DEADLOCK DETECTED! Circular wait among PIDs: {unique_pids}")
            return unique_pids

        return []