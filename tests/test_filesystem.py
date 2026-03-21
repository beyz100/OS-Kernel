from core.file_system import FileSystem


def test_file_system_operations():
    fs = FileSystem()

    success, latency = fs.create("test.txt", "ProcessA")
    assert success is True
    
    success, latency = fs.create("test.txt", "ProcessB")
    assert success is False

    success, latency = fs.write("test.txt", "Hello OS", "ProcessA")
    assert success is True
    assert fs.files["test.txt"].size == 8

    data, latency = fs.read("test.txt", "ProcessB")
    assert data == "Hello OS"

    assert fs.delete("test.txt", "ProcessA") is True
    
    data, latency = fs.read("test.txt", "ProcessA")
    assert data is None
