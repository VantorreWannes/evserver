import shutil
from typing import TYPE_CHECKING

import aiofiles

if TYPE_CHECKING:
    from pathlib import Path

    from evserver.types import Hash, ObjectType, UserId


class Archive:
    """Filesystem-backed store of content-addressed objects, partitioned by user and type."""  # noqa: E501

    def __init__(self, root: Path) -> None:
        self.root = root

    def _path(self, user_id: UserId, obj_type: ObjectType, obj_hash: Hash) -> Path:
        return self.root / user_id / obj_type / obj_hash

    async def contains_user(self, user_id: UserId) -> bool:
        return (self.root / user_id).is_dir()

    async def add_user(self, user_id: UserId) -> None:
        (self.root / user_id).mkdir(parents=True, exist_ok=False)

    async def delete_user(self, user_id: UserId) -> None:
        shutil.rmtree(self.root / user_id, ignore_errors=True)

    async def contains(
        self, user_id: UserId, obj_type: ObjectType, obj_hash: Hash
    ) -> bool:
        return self._path(user_id, obj_type, obj_hash).is_file()

    async def get(self, user_id: UserId, obj_type: ObjectType, obj_hash: Hash) -> bytes:
        async with aiofiles.open(self._path(user_id, obj_type, obj_hash), "rb") as f:
            return await f.read()

    async def put(
        self, user_id: UserId, obj_type: ObjectType, obj_hash: Hash, data: bytes
    ) -> None:
        path = self._path(user_id, obj_type, obj_hash)
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "wb") as f:
            await f.write(data)

    async def delete(
        self, user_id: UserId, obj_type: ObjectType, obj_hash: Hash
    ) -> None:
        self._path(user_id, obj_type, obj_hash).unlink(missing_ok=True)

    async def hashes(self, user_id: UserId, obj_type: ObjectType) -> list[Hash]:
        directory = self.root / user_id / obj_type
        if not directory.is_dir():
            return []
        return sorted(p.name for p in directory.iterdir() if p.is_file())
