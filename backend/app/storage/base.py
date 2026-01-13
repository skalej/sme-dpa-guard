from typing import Protocol


class StorageClient(Protocol):
    def put_bytes(self, key: str, data: bytes, content_type: str) -> None:
        ...
