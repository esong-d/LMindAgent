

from abc import ABC, abstractmethod
from io import BufferedReader


class FileStorage(ABC):
    @abstractmethod
    def save_bytes(self, *, data: bytes, original_filename: str) -> tuple[str, int]:
        raise NotImplementedError

    @abstractmethod
    def open(self, storage_path: str) -> BufferedReader:
        raise NotImplementedError

    @abstractmethod
    def delete(self, storage_path: str) -> None:
        raise NotImplementedError
