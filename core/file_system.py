from utils.logger import OSLogger


class File:
    def __init__(self, name: str):
        self.name = name
        self.content = ""
        self.size = 0


class FileSystem:
    def __init__(self):
        self.files = {}

    def create(self, filename: str, process_name: str) -> bool:
        if filename in self.files:
            OSLogger.log("FileSystem", f"Error: '{filename}' already exists.")
            return False

        self.files[filename] = File(filename)
        OSLogger.log("FileSystem", f"Created file '{filename}' (Owner: {process_name})")
        return True

    def write(self, filename: str, data: str, process_name: str) -> bool:
        if filename not in self.files:
            OSLogger.log("FileSystem", f"Error: Cannot write, '{filename}' not found.")
            return False

        self.files[filename].content += data
        self.files[filename].size = len(self.files[filename].content)
        OSLogger.log("FileSystem", f"Write to '{filename}' by {process_name} (+{len(data)} bytes)")
        return True

    def read(self, filename: str, process_name: str):
        if filename not in self.files:
            OSLogger.log("FileSystem", f"Error: Cannot read, '{filename}' not found.")
            return None

        data = self.files[filename].content
        OSLogger.log("FileSystem", f"Read from '{filename}' by {process_name} ({len(data)} bytes)")
        return data

    def delete(self, filename: str, process_name: str) -> bool:
        if filename in self.files:
            del self.files[filename]
            OSLogger.log("FileSystem", f"Deleted file '{filename}' (Action by: {process_name})")
            return True
        return False