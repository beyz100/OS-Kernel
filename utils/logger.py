class OSLogger:
    @staticmethod
    def log(component: str, message: str, tick: int = None):
        timestamp = f"[Tick: {tick:02}] " if tick is not None else ""
        print(f"{timestamp}[{component}] {message}")