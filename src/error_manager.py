class ErrorManager:
    def __init__(self, log_callback=None):
        # Optional callback used to route log messages externally
        self.log_callback = log_callback
        pass

    def set_log_callback(self, log_callback):
        # Update the callback used to handle emitted log messages
        self.log_callback = log_callback
        pass

    def _emit(self, level: str, msg: str):
        # Internal helper to format and send a log message with a given severity level
        full_msg = f"[{level}] {msg}"
        if self.log_callback is not None:
            # If a callback is provided, delegate message handling to it
            self.log_callback(full_msg)
        else:
            # Fallback to standard output if no callback is defined
            print(full_msg)
        pass

    def info(self, msg: str):
        # Emit an informational message (normal operation feedback)
        self._emit("INFO", msg)
        pass

    def warning(self, msg: str):
        # Emit a warning message (non-fatal abnormal condition)
        self._emit("WARNING", msg)
        pass

    def error(self, msg: str):
        # Emit an error message (problem that likely requires user attention)
        self._emit("ERROR", msg)
        pass
