class ComparisonError(Exception):
    def __init__(self, message, differences=None):
        super().__init__(message)
        self.differences = differences if differences else []
        self.message = message

    def __str__(self):
        error = f"{super().__str__()}\n"
        differences = "\n\n".join(str(d) for d in self.differences)
        return error + differences
