from dataclasses import dataclass
from typing import Self

@dataclass
class Question:
    """
    Wrapper for a question retrieved from PocketBase.
    """
    id: str
    question: str

    @classmethod
    def from_pb_record(cls, record) -> Self:
        """
        Creates a Question class from a pocketbase record.
        """
        return cls(
            id=record.id,
            question=getattr(record, "question", None),
        )
