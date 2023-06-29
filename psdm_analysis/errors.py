import traceback


class ComparisonError(Exception):
    def __init__(self, message="", errors=None):
        super().__init__(message)
        self.errors = errors or []
        self.tracebacks = [
            traceback.format_exception(type(e), e, e.__traceback__) for e in self.errors
        ]

    def __str__(self):
        error_messages = [f"{type(e).__name__}: {str(e)}" for e in self.errors]
        formatted_tracebacks = ["".join(tb) for tb in self.tracebacks]
        error_report = "\n".join(
            f"Error: {msg}\nTraceback:\n{tb}"
            for msg, tb in zip(error_messages, formatted_tracebacks)
        )
        return f"{super().__str__()}:\n{error_report}"
