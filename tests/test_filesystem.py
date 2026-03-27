from core.file_system import FileSystem


def test_file_system_operations():
    fs = FileSystem()

    success, latency = fs.create("test.txt", "ProcessA")
    assert success is True
    assert latency == 1
    
    success, latency = fs.create("test.txt", "ProcessB")
    assert success is False

    success, latency = fs.write("test.txt", "Hello OS", "ProcessA")
    assert success is True
    assert latency == 2
    assert fs.files["test.txt"].size == 8

    data, latency = fs.read("test.txt", "ProcessB")
    assert data == "Hello OS"
    assert latency == 0  # Cache hit

    data, latency = fs.read("test.txt", "ProcessC")
    assert data == "Hello OS"
    assert latency == 0

    assert fs.delete("test.txt", "ProcessA") is True
    
    data, latency = fs.read("test.txt", "ProcessA")
    assert data is None


def test_file_ownership():
    fs = FileSystem()
    
    fs.create("secure.log", "ProcessA")
    
    owner = fs.get_file_owner("secure.log")
    assert owner == "ProcessA"
    
    owner = fs.get_file_owner("nonexistent.log")
    assert owner is None


def test_cache_management():
    fs = FileSystem(cache_size=2)
    
    fs.create("file1.txt", "P1")
    fs.write("file1.txt", "Content1", "P1")
    
    fs.create("file2.txt", "P2")
    fs.write("file2.txt", "Content2", "P2")
    
    fs.create("file3.txt", "P3")
    fs.write("file3.txt", "Content3", "P3")
    
    assert len(fs.cache) == 2
    assert "file1.txt" not in fs.cache
    assert "file2.txt" in fs.cache
    assert "file3.txt" in fs.cache


def test_file_size_tracking():
    fs = FileSystem()
    
    fs.create("data.bin", "ProcessA")
    assert fs.get_file_size("data.bin") == 0
    
    fs.write("data.bin", "Hello", "ProcessA")
    assert fs.get_file_size("data.bin") == 5
    
    fs.write("data.bin", "World", "ProcessA")
    assert fs.get_file_size("data.bin") == 10
    
    # Non-existent file
    assert fs.get_file_size("nonexistent.txt") == 0


def test_file_exists():
    fs = FileSystem()
    
    assert fs.exists("test.txt") is False
    
    fs.create("test.txt", "ProcessA")
    assert fs.exists("test.txt") is True
    
    fs.delete("test.txt", "ProcessA")
    assert fs.exists("test.txt") is False


def test_list_files():
    fs = FileSystem()
    
    assert fs.list_files() == []
    
    fs.create("file1.txt", "P1")
    fs.create("file2.txt", "P2")
    
    files = fs.list_files()
    assert len(files) == 2
    assert "file1.txt" in files
    assert "file2.txt" in files


def test_fs_stats():
    fs = FileSystem(cache_size=3)
    
    stats = fs.get_stats()
    assert stats["total_files"] == 0
    assert stats["total_size"] == 0
    assert stats["cache_size"] == 3
    
    fs.create("file1.txt", "P1")
    fs.write("file1.txt", "Hello", "P1")
    
    fs.create("file2.txt", "P2")
    fs.write("file2.txt", "World", "P2")
    
    stats = fs.get_stats()
    assert stats["total_files"] == 2
    assert stats["total_size"] == 10


def test_multiple_writes_and_reads():
    fs = FileSystem()
    
    fs.create("log.txt", "Logger")
    
    # Multiple writes
    fs.write("log.txt", "[START] ", "Logger")
    fs.write("log.txt", "Process A ", "Logger")
    fs.write("log.txt", "Process B", "Logger")
    
    assert fs.get_file_size("log.txt") == 27
    
    data, _ = fs.read("log.txt", "Monitor")
    assert data == "[START] Process A Process B"

