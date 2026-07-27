from typing import TYPE_CHECKING

import dill
from blake3 import blake3
from pydantic.dataclasses import dataclass

if TYPE_CHECKING:
    from pathlib import Path

Digest = str
UserId = str
WorkspaceId = Digest
SnapshotId = Digest
ManifestId = Digest
ReferenceId = Digest


@dataclass(frozen=True, slots=True)
class Reference:
    file_path: Path
    content_digest: Digest

    @property
    def id(self) -> ReferenceId:
        return blake3(dill.dumps((self.file_path, self.content_digest))).hexdigest()


@dataclass(frozen=True, slots=True)
class Manifest:
    files: tuple[Reference, ...]

    @property
    def id(self) -> ManifestId:
        return blake3(dill.dumps(self.files)).hexdigest()


@dataclass(frozen=True, slots=True)
class Snapshot:
    comment: str | None
    manifest: Manifest

    @property
    def id(self) -> SnapshotId:
        return blake3(dill.dumps(self.comment, self.manifest)).hexdigest()


@dataclass(frozen=True, slots=True)
class Workspace:
    snapshots: tuple[Snapshot, ...]
    directory: Path

    @property
    def id(self) -> SnapshotId:
        return blake3(dill.dumps(self.directory)).hexdigest()
