from typing import Self

class User:
    id: str
    email: str
    name: str | None = None
    is_admin: bool = False

    def __init__(self, id:str, email: str, name: str | None = None, is_admin: bool | None = None):
        self.id = id
        self.email = email
        self.name = name
        self.is_admin = bool(is_admin)
    
    @classmethod
    def from_pb_record(cls, record) -> Self:
        return cls(
            id=record.id,
            email=record.email,
            name=getattr(record, "name", None),
            is_admin=bool(getattr(record, "admin", False)),
        )