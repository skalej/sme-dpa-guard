class InvalidStatusTransition(Exception):
    def __init__(self, from_status, to_status) -> None:
        message = f"Invalid transition: {from_status} -> {to_status}"
        super().__init__(message)
        self.from_status = from_status
        self.to_status = to_status
