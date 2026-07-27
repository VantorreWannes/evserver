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
ContentId = Digest


@dataclass(frozen=True, slots=True)
class Reference:
    file_path: Path
    content_digest: ContentId

    @property
    def id(self) -> ReferenceId:
        return blake3(dill.dumps((self.file_path, self.content_digest))).hexdigest()


@dataclass(frozen=True, slots=True)
class Manifest:
    reference_ids: tuple[ReferenceId, ...]

    @property
    def id(self) -> ManifestId:
        return blake3(dill.dumps(self.reference_ids)).hexdigest()


@dataclass(frozen=True, slots=True)
class Snapshot:
    comment: str | None
    manifest_id: ManifestId

    @property
    def id(self) -> SnapshotId:
        return blake3(dill.dumps(self.comment, self.manifest_id)).hexdigest()


@dataclass(frozen=True, slots=True)
class Workspace:
    directory: Path
    snapshot_ids: tuple[SnapshotId, ...]

    @property
    def id(self) -> SnapshotId:
        return blake3(dill.dumps(self.directory)).hexdigest()


@dataclass(frozen=True, slots=True)
class User:
    id: UserId
    workspace_ids: set[WorkspaceId]
