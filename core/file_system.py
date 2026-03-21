from utils.logger import OSLogger


class File:
    def __init__(self, name: str):
        self.name = name
        self.content = ""
        self.size = 0


class FileSystem:
    def __init__(self, cache_size: int = 3):
        self.files = {}

        self.cache = {}
        self.cache_size = cache_size
        self.cache_queue = [] 

    def _manage_cache(self, filename: str):
        if filename not in self.cache:
            if len(self.cache) >= self.cache_size:
                evicted = self.cache_queue.pop(0)
                del self.cache[evicted]
                OSLogger.log("FileSystem", f"Cache FULL! Evicted '{evicted}'.")

            self.cache_queue.append(filename)

    def create(self, filename: str, process_name: str) -> tuple[bool, int]:
        if filename in self.files:
            return False, 0

        self.files[filename] = File(filename)
        OSLogger.log("FileSystem", f"Created file '{filename}' (Owner: {process_name})")
        return True, 1  

    def write(self, filename: str, data: str, process_name: str) -> tuple[bool, int]:
        if filename not in self.files:
            return False, 0

        self.files[filename].content += data
        self.files[filename].size = len(self.files[filename].content)

        self._manage_cache(filename)
        self.cache[filename] = self.files[filename].content

        OSLogger.log("FileSystem", f"Disk WRITE to '{filename}' by {process_name} (+{len(data)} bytes)")
        return True, 2  

    def read(self, filename: str, process_name: str) -> tuple[str | None, int]:
        if filename not in self.files:
            return None, 0

        if filename in self.cache:
            OSLogger.log("FileSystem", f"CACHE HIT! Read '{filename}' by {process_name} (Fast)")
            return self.cache[filename], 0  

        OSLogger.log("FileSystem", f"CACHE MISS! Read '{filename}' from disk by {process_name} (Slow)")

        self._manage_cache(filename)
        self.cache[filename] = self.files[filename].content

        return self.files[filename].content, 2  

    def delete(self, filename: str, process_name: str) -> bool:
        if filename not in self.files:
            OSLogger.log("FileSystem", f"Error: Cannot delete, '{filename}' not found.")
            return False
        
        del self.files[filename]
        
        if filename in self.cache:
            del self.cache[filename]
            if filename in self.cache_queue:
                self.cache_queue.remove(filename)
        
        OSLogger.log("FileSystem", f"Deleted file '{filename}' (Action by: {process_name})")
        return True
