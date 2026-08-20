from pathlib import Path  # noqa: TC003
from typing import TYPE_CHECKING

import dill

if TYPE_CHECKING:
    from evserver.types import Id


class DirectoryStore[K, V]:
    def __init__(self, root: Path) -> None:
        root.mkdir(parents=True, exist_ok=True)
        self.root = root

    def _path(self, key: Id) -> Path:
        return self.root / key

    async def contains(self, key: Id) -> bool:
        return self._path(key).exists()

    async def set(self, key: Id, value: V) -> None:
        path = self._path(key)
        with path.open("wb") as f:
            dill.dump(value, f)

    async def get(self, key: Id) -> V:
        path = self._path(key)
        with path.open("rb") as f:
            return dill.load(f)  # noqa: S301

    async def delete(self, key: Id) -> None:
        path = self._path(key)
        path.unlink()
