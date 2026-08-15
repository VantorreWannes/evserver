import shutil
from collections.abc import Hashable
from typing import TYPE_CHECKING

import aiofiles
import dill

if TYPE_CHECKING:
    from pathlib import Path


class FileStore[K: Hashable, V]:
    def __init__(self, path: Path) -> None:
        self.path = path

    @classmethod
    def load(cls, path: Path) -> dict[K, V]:
        if path.exists():
            return dill.loads(path.read_bytes())  # noqa: S301
        return {}

    @classmethod
    def save(cls, path: Path, key_values: dict[K, V]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(dill.dumps(key_values))

    async def get(self, key: K) -> V:
        return FileStore[K, V].load(self.path)[key]

    async def set(self, key: K, value: V) -> None:
        key_values = FileStore[K, V].load(self.path)
        key_values[key] = value
        FileStore[K, V].save(self.path, key_values)

    async def delete(self, key: K) -> None:
        key_values = FileStore[K, V].load(self.path)
        key_values.pop(key)
        FileStore[K, V].save(self.path, key_values)

    async def keys(self) -> tuple[K, ...]:
        return tuple(FileStore[K, V].load(self.path).keys())

    async def contains(self, key: K) -> bool:
        return key in FileStore[K, V].load(self.path)


class BlobStore:
    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def _path(self, user_id: str, blob_hash: str) -> Path:
        return self.directory / user_id / blob_hash

    async def contains(self, user_id: str, blob_hash: str) -> bool:
        return self._path(user_id, blob_hash).is_file()

    async def get(self, user_id: str, blob_hash: str) -> bytes:
        async with aiofiles.open(self._path(user_id, blob_hash), mode="rb") as f:
            return await f.read()

    async def set(self, user_id: str, blob_hash: str, data: bytes) -> None:
        path = self._path(user_id, blob_hash)
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, mode="wb") as f:
            await f.write(data)

    async def delete(self, user_id: str, blob_hash: str) -> None:
        self._path(user_id, blob_hash).unlink(missing_ok=True)

    async def delete_user(self, user_id: str) -> None:
        shutil.rmtree(self.directory / user_id, ignore_errors=True)
