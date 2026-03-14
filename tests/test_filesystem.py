from core.file_system import FileSystem


def test_file_system_operations():
    fs = FileSystem()

    assert fs.create("test.txt", "ProcessA") is True
    assert fs.create("test.txt", "ProcessB") is False

    assert fs.write("test.txt", "Hello OS", "ProcessA") is True
    assert fs.files["test.txt"].size == 8

    data = fs.read("test.txt", "ProcessB")
    assert data == "Hello OS"

    assert fs.delete("test.txt", "ProcessA") is True
    assert fs.read("test.txt", "ProcessA") is None