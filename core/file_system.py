import math
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
        self.corrupted = False


class Directory:
    """A node in the file-system tree. Children are name -> File | Directory."""

    def __init__(self, name: str, parent: "Directory | None" = None):
        self.name = name
        self.parent = parent
        self.children: dict[str, "File | Directory"] = {}

    @property
    def path(self) -> str:
        if self.parent is None:
            return "/"
        parent_path = self.parent.path
        sep = "" if parent_path.endswith("/") else "/"
        return f"{parent_path}{sep}{self.name}"


class FileSystem:

    def __init__(self, cache_size: int = 3,
                 max_blocks: int | None = None,
                 block_size: int = 512):
        self.files = {}

        self.cache = {}
        self.cache_size = cache_size
        self.cache_queue = []

        self.file_locks = {}

        # Disk-quota support (Bartu integration)
        self.max_blocks = max_blocks   # None = unlimited
        self.block_size = block_size   # bytes per block
        self._used_blocks = 0

        # Hierarchical namespace. Files created with bare names live directly
        # under root; nested paths are resolved through this tree.
        self.root = Directory("/")

        limit_str = f"{max_blocks} blocks × {block_size} B" if max_blocks else "unlimited"
        OSLogger.log("FileSystem", f"Initialized with cache_size={cache_size}, disk={limit_str}")

    # ------------------------------------------------------------------ paths
    @staticmethod
    def _split_path(path: str) -> tuple[list[str], str]:
        """'/var/log/x.log' -> (['var', 'log'], 'x.log'); 'x.log' -> ([], 'x.log')."""
        parts = [p for p in path.split("/") if p]
        if not parts:
            return [], ""
        return parts[:-1], parts[-1]

    def _resolve_dir(self, dir_parts: list[str], create_missing: bool = False) -> "Directory | None":
        cursor = self.root
        for part in dir_parts:
            child = cursor.children.get(part)
            if isinstance(child, Directory):
                cursor = child
            elif child is None and create_missing:
                new_dir = Directory(part, parent=cursor)
                cursor.children[part] = new_dir
                cursor = new_dir
            else:
                return None
        return cursor

    # ------------------------------------------------------------------ directories
    def mkdir(self, path: str) -> bool:
        dir_parts, name = self._split_path(path)
        if not name:
            OSLogger.log("FileSystem", f"mkdir FAILED: invalid path '{path}'")
            return False
        parent = self._resolve_dir(dir_parts, create_missing=False)
        if parent is None:
            OSLogger.log("FileSystem", f"mkdir FAILED: parent of '{path}' does not exist")
            return False
        if name in parent.children:
            OSLogger.log("FileSystem", f"mkdir FAILED: '{path}' already exists")
            return False
        new_dir = Directory(name, parent=parent)
        parent.children[name] = new_dir
        OSLogger.log("FileSystem", f"Created directory '{new_dir.path}'")
        return True

    def list_dir(self, path: str = "/") -> list[str]:
        if path in ("", "/"):
            return list(self.root.children.keys())
        dir_parts, name = self._split_path(path)
        target = self._resolve_dir(dir_parts + ([name] if name else []), create_missing=False)
        if target is None:
            return []
        return list(target.children.keys())

    # ------------------------------------------------------------------ cache
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

    # ------------------------------------------------------------------ locks
    def _acquire_lock(self, filename: str, process_id: int) -> bool:
        if filename in self.file_locks and self.file_locks[filename] != process_id:
            return False
        self.file_locks[filename] = process_id
        return True

    def _release_lock(self, filename: str) -> None:
        if filename in self.file_locks:
            del self.file_locks[filename]

    # ------------------------------------------------------------------ blocks
    def _blocks_needed(self, size: int) -> int:
        if size == 0:
            return 0
        return math.ceil(size / self.block_size)

    def _recalculate_used_blocks(self) -> None:
        self._used_blocks = sum(self._blocks_needed(f.size) for f in self.files.values())

    # ------------------------------------------------------------------ CRUD
    def create(self, filename: str, process_name: str) -> tuple[bool, int]:
        if filename in self.files:
            OSLogger.log("FileSystem", f"Create FAILED: File '{filename}' already exists")
            return False, 0

        dir_parts, basename = self._split_path(filename)
        if not basename:
            OSLogger.log("FileSystem", f"Create FAILED: invalid filename '{filename}'")
            return False, 0
        parent_dir = self._resolve_dir(dir_parts, create_missing=False)
        if parent_dir is None:
            OSLogger.log("FileSystem", f"Create FAILED: directory for '{filename}' does not exist")
            return False, 0
        if basename in parent_dir.children:
            OSLogger.log("FileSystem", f"Create FAILED: '{filename}' already exists in directory")
            return False, 0

        file_obj = File(basename, process_name)
        self.files[filename] = file_obj
        parent_dir.children[basename] = file_obj
        OSLogger.log("FileSystem", f"Created file '{filename}' (Owner: {process_name})")
        return True, 1

    def write(self, filename: str, data: str, process_name: str) -> tuple[bool, int]:
        if filename not in self.files:
            OSLogger.log("FileSystem", f"Write FAILED: File '{filename}' not found")
            return False, 0

        if not self._acquire_lock(filename, hash(process_name)):
            OSLogger.log("FileSystem", f"Write BLOCKED: '{filename}' is locked by another process")
            return False, 0

        file_obj = self.files[filename]

        # Block writes to corrupted files
        if file_obj.corrupted:
            OSLogger.log("FileSystem", f"Write BLOCKED: '{filename}' is corrupted")
            return False, 0

        # Enforce disk-block quota when max_blocks is set
        if self.max_blocks is not None:
            blocks_needed = math.ceil(len(data) / self.block_size)
            if self._used_blocks + blocks_needed > self.max_blocks:
                OSLogger.log(
                    "FileSystem",
                    f"DISK FULL: Write to '{filename}' by {process_name} REJECTED "
                    f"(used={self._used_blocks}/{self.max_blocks} blocks)."
                )
                return False, 0
            self._used_blocks += blocks_needed

        file_obj.content += data
        file_obj.size = len(file_obj.content)

        self._manage_cache(filename)
        self.cache[filename] = file_obj.content

        OSLogger.log("FileSystem", f"Disk WRITE to '{filename}' by {process_name} (+{len(data)} bytes)")
        self._release_lock(filename)
        return True, 2

    def read(self, filename: str, process_name: str) -> tuple[str | None, int]:
        if filename not in self.files:
            OSLogger.log("FileSystem", f"Read FAILED: File '{filename}' not found")
            return None, 0

        if not self._acquire_lock(filename, hash(process_name)):
            OSLogger.log("FileSystem", f"Read BLOCKED: '{filename}' is locked by another process")
            return None, 0

        file_obj = self.files[filename]

        # Corrupted flag set by corrupt_file()
        if file_obj.corrupted:
            OSLogger.log("FileSystem", f"CORRUPTED FILE: '{filename}' cannot be read (marked corrupted).")
            return None, 0

        if filename in self.cache:
            data = self.cache[filename]
            if filename in self.cache_queue:
                self.cache_queue.remove(filename)
            self.cache_queue.append(filename)
            OSLogger.log("FileSystem", f"Cache HIT on '{filename}' by {process_name} — no I/O block, served from memory")
            self._check_null_corruption(filename, data)
            self._release_lock(filename)
            return data, 0

        data = file_obj.content
        self._manage_cache(filename)
        self.cache[filename] = data
        OSLogger.log("FileSystem", f"Cache MISS on '{filename}' by {process_name}")
        self._check_null_corruption(filename, data)
        self._release_lock(filename)
        return data, 1

    def _check_null_corruption(self, filename: str, data: str) -> bool:
        """Warn if content is all null bytes (silent on-disk corruption)."""
        if data and all(c == "\x00" for c in data):
            OSLogger.log(
                "FileSystem",
                f"CORRUPTED FILE DETECTED: '{filename}' contains only null bytes. Skipping."
            )
            return True
        return False

    def corrupt_file(self, filename: str) -> bool:
        """Mark a file as corrupted and inject null bytes to simulate disk corruption."""
        if filename not in self.files:
            OSLogger.log("FileSystem", f"corrupt_file FAILED: '{filename}' not found")
            return False

        file_obj = self.files[filename]
        file_obj.corrupted = True
        # Also inject null bytes so null-byte detection path is hit too
        size = max(file_obj.size, 1)
        file_obj.content = "\x00" * size

        # Invalidate cache
        if filename in self.cache:
            del self.cache[filename]
        if filename in self.cache_queue:
            self.cache_queue.remove(filename)

        OSLogger.log("FileSystem", f"File '{filename}' CORRUPTED — {size} null bytes injected.")
        return True

    def delete(self, filename: str, process_name: str) -> bool:
        if filename not in self.files:
            OSLogger.log("FileSystem", f"Delete FAILED: File '{filename}' not found")
            return False

        del self.files[filename]

        # Remove the file from its parent directory's children
        dir_parts, basename = self._split_path(filename)
        parent_dir = self._resolve_dir(dir_parts, create_missing=False)
        if parent_dir is not None and basename in parent_dir.children:
            del parent_dir.children[basename]

        if filename in self.cache:
            del self.cache[filename]
            if filename in self.cache_queue:
                self.cache_queue.remove(filename)

        self._release_lock(filename)
        self._recalculate_used_blocks()

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
        corrupted_count = sum(1 for f in self.files.values() if f.corrupted)
        return {
            "total_files": len(self.files),
            "total_size": total_size,
            "cache_items": len(self.cache),
            "cache_size": self.cache_size,
            "used_blocks": self._used_blocks,
            "max_blocks": self.max_blocks,
            "corrupted_files": corrupted_count,
        }