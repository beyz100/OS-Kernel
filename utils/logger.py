class OSLogger:
    COLORS = {
        "RESET": "\033[0m",
        "CYAN": "\033[96m",
        "GREEN": "\033[92m",
        "YELLOW": "\033[93m",
        "RED": "\033[91m",
        "MAGENTA": "\033[95m",
        "BLUE": "\033[94m"
    }

    @staticmethod
    def log(component: str, message: str, tick: int = None):
        color = OSLogger.COLORS["RESET"]
        tag = ""
        msg_upper = message.upper()
        
        if "PAGE FAULT" in msg_upper or "EVICTED" in msg_upper or "TRAP" in msg_upper or "FETCH" in msg_upper or "DEADLOCK" in msg_upper:
            color = OSLogger.COLORS["RED"]
            tag = "[CRITICAL] " if "DEADLOCK" in msg_upper else "[PAGE FAULT] "
        elif "MUTEX" in msg_upper or "ACQUIRE" in msg_upper or "RELEASE" in msg_upper or "CONTENTION" in msg_upper or "LOCK '" in msg_upper:
            color = OSLogger.COLORS["MAGENTA"]
            tag = "[LOCK EVENT] "
        elif "I/O" in msg_upper or "FILE" in msg_upper and ("LATENCY" in msg_upper or "BYTES" in msg_upper) or "DISK" in msg_upper:
            color = OSLogger.COLORS["BLUE"]
            tag = "[I/O EVENT] "
        elif "DISPATCH" in msg_upper or "PREEMPT" in msg_upper or "CONTEXT SWITCH" in msg_upper or "RUNNING" in msg_upper:
            color = OSLogger.COLORS["GREEN"]
            tag = "[CONTEXT SWITCH] "
        elif "WAIT" in msg_upper or "BLOCK" in msg_upper:
            color = OSLogger.COLORS["YELLOW"]
            tag = "[WAIT EVENT] "

        timestamp = f"[Tick: {tick:02}] " if tick is not None else "[Tick: --] "
        print(f"{color}{timestamp}[{component:^10}] {tag}{message}{OSLogger.COLORS['RESET']}")