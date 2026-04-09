from utils.logger import OSLogger


class IORequest:
    def __init__(self, pid: int, op: str, filename: str, delay: int, success: bool = True, data=None):
        self.pid = pid
        self.op = op
        self.filename = filename
        self.delay = delay
        self.success = success
        self.data = data

    @property
    def should_block(self) -> bool:
        return self.delay > 0


class File:
    def __init__(self, name: str, owner: str):
        self.name = name
        self.owner = owner
        self.content = ""
        self.size = 0
        self.created_tick = 0
        self.modified_tick = 0


class FileSystem:

    def __init__(self, cache_size: int = 3):
        self.files = {}

        self.cache = {}
        self.cache_size = cache_size
        self.cache_queue = []

        self.file_locks = {}

        OSLogger.log("FileSystem", f"Initialized with cache_size={cache_size}")

    def _manage_cache(self, filename: str) -> None:
        if filename in self.cache_queue:
            self.cache_queue.remove(filename)
            self.cache_queue.append(filename)
            return

        if len(self.cache) >= self.cache_size:
            evicted = self.cache_queue.pop(0)
            del self.cache[evicted]
            OSLogger.log("FileSystem", f"Cache FULL! Evicted '{evicted}' (LRU)")

        self.cache_queue.append(filename)

    def _acquire_lock(self, filename: str, process_id: int) -> bool:
        if filename in self.file_locks and self.file_locks[filename] != process_id:
            return False
        self.file_locks[filename] = process_id
        return True

    def _release_lock(self, filename: str) -> None:
        if filename in self.file_locks:
            del self.file_locks[filename]

    def create(self, filename: str, process_name: str) -> tuple[bool, int]:
        if filename in self.files:
            OSLogger.log("FileSystem", f"Create FAILED: File '{filename}' already exists")
            return False, 0

        self.files[filename] = File(filename, process_name)
        OSLogger.log("FileSystem", f"Created file '{filename}' (Owner: {process_name})")
        return True, 1

    def write(self, filename: str, data: str, process_name: str) -> tuple[bool, int]:
        if filename not in self.files:
            OSLogger.log("FileSystem", f"Write FAILED: File '{filename}' not found")
            return False, 0

        file_obj = self.files[filename]

        file_obj.content += data
        file_obj.size = len(file_obj.content)

        self._manage_cache(filename)
        self.cache[filename] = file_obj.content

        OSLogger.log("FileSystem", f"Disk WRITE to '{filename}' by {process_name} (+{len(data)} bytes)")
        return True, 2

    def read(self, filename: str, process_name: str) -> tuple[str | None, int]:
        if filename not in self.files:
            OSLogger.log("FileSystem", f"Read FAILED: File '{filename}' not found")
            return None, 0

        if filename in self.cache:
            data = self.cache[filename]

            if filename in self.cache_queue:
                self.cache_queue.remove(filename)
            self.cache_queue.append(filename)

            OSLogger.log("FileSystem", f"Cache HIT on '{filename}' by {process_name}")
            return data, 0

        data = self.files[filename].content

        self._manage_cache(filename)
        self.cache[filename] = data

        OSLogger.log("FileSystem", f"Cache MISS on '{filename}' by {process_name}")
        return data, 1

    def delete(self, filename: str, process_name: str) -> bool:
        if filename not in self.files:
            OSLogger.log("FileSystem", f"Delete FAILED: File '{filename}' not found")
            return False

        del self.files[filename]

        if filename in self.cache:
            del self.cache[filename]
            if filename in self.cache_queue:
                self.cache_queue.remove(filename)

        self._release_lock(filename)

        OSLogger.log("FileSystem", f"Deleted file '{filename}' (Action by: {process_name})")
        return True

    def exists(self, filename: str) -> bool:
        return filename in self.files

    def get_file_size(self, filename: str) -> int:
        if filename in self.files:
            return self.files[filename].size
        return 0

    def get_file_owner(self, filename: str) -> str | None:
        if filename in self.files:
            return self.files[filename].owner
        return None

    def list_files(self) -> list[str]:
        return list(self.files.keys())

    def request_read(self, process, filename: str) -> IORequest:
        data, delay = self.read(filename, process.name)
        OSLogger.log("FileSystem", f"PID={process.pid} requested READ on '{filename}' (delay={delay})")
        return IORequest(
            pid=process.pid,
            op="read",
            filename=filename,
            delay=delay,
            success=(data is not None),
            data=data
        )

    def request_write(self, process, filename: str, data: str) -> IORequest:
        success, delay = self.write(filename, data, process.name)
        OSLogger.log("FileSystem", f"PID={process.pid} requested WRITE on '{filename}' (delay={delay})")
        return IORequest(
            pid=process.pid,
            op="write",
            filename=filename,
            delay=delay,
            success=success
        )

    def get_stats(self) -> dict:
        total_size = sum(f.size for f in self.files.values())
        return {
            "total_files": len(self.files),
            "total_size": total_size,
            "cache_items": len(self.cache),
            "cache_size": self.cache_size
        }