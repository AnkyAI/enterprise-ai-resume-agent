from abc import ABC, abstractmethod
from typing import Generic, TypeVar

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class Agent(ABC, Generic[InputT, OutputT]):
    name: str

    @abstractmethod
    async def run(self, input_data: InputT) -> OutputT:
        """Execute one isolated pipeline responsibility."""
