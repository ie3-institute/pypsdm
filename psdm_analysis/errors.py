class ComparisonError(Exception):
    def __init__(self, message, errors=None):
        super().__init__(message)
        self.differences = errors if errors else []
        self.message = message

    def __str__(self):
        error = f"{super().__str__()}\n"
        differences = "\n\n".join(str(d) for d in self.differences)
        return error + differences
