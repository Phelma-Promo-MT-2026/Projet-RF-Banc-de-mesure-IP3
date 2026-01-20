class ErrorManager:
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        pass
    def set_log_callback(self, log_callback):
        self.log_callback = log_callback
        pass
    def _emit(self, level: str, msg: str):
        full_msg = f"[{level}] {msg}"
        if self.log_callback is not None:
            self.log_callback(full_msg)
        else:
            print(full_msg)
        pass
    def info(self, msg: str):
        self._emit("INFO", msg)
        pass
    def warning(self, msg: str):
        self._emit("WARNING", msg)
        pass
    def error(self, msg: str):
        self._emit("ERROR", msg)
        pass