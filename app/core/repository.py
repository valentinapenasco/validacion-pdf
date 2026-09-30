from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    @abstractmethod
    async def save(self, entity: T) -> T:
        raise NotImplementedError


class InMemoryRepository(Repository[T]):
    def __init__(self) -> None:
        self._storage: dict[str, T] = {}

    async def save(self, entity: T) -> T:
        key = getattr(entity, "id", id(entity))
        self._storage[str(key)] = entity
        return entity
