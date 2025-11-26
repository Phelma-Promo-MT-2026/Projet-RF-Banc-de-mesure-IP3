class error_manager:
    """
    Error manager class
    """

    def __init__(self, verbose=True):
        self.verbose = verbose
        self.errors = []  # logs

    def log_error(self, message):
        """Add error to log and display."""
        self.errors.append(message)
        if self.verbose:
            print(f"[Error] {message}")

    def check_type(self, var, expected_type, var_name="variable"):
        if not isinstance(var, expected_type):
            self.log_error(f"{var_name} must be type {expected_type.__name__}, receveid {type(var).__name__}")
            return False
        return True

    def check_range(self, value, min_val=None, max_val=None, var_name="value"):
        if not isinstance(value, (int, float)):
            self.log_error(f"{var_name} must be numeric (int ou float).")
            return False
        if min_val is not None and value < min_val:
            self.log_error(f"{var_name} too low ({value} < {min_val})")
            return False
        if max_val is not None and value > max_val:
            self.log_error(f"{var_name} too high ({value} > {max_val})")
            return False
        return True

    def check_choice(self, value, valid_choices, var_name="value"):
        if value not in valid_choices:
            self.log_error(f"{var_name} must be among {valid_choices}, received {value}")
            return False
        return True

    def reset_errors(self):
        self.errors = []

    def has_errors(self):
        return len(self.errors) > 0

    def get_errors(self):
        return self.errors
