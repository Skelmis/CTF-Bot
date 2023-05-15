from alaric.types import ObjectId


class User:
    def __init__(self, _id, flags: list[str]):
        self._id: ObjectId = _id
        self.flags: list[str] = flags

    def as_filter(self) -> dict:
        return {"_id": self._id}

    def as_dict(self) -> dict:
        return {"_id": self._id, "flags": self.flags}
