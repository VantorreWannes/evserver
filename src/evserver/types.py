from hashlib import sha3_512
from pathlib import Path  # noqa: TC003

from pydantic.dataclasses import dataclass

type Id = str
UserId = Id
WorkspaceId = Id
SnapshotId = Id
ManifestId = Id
ReferenceId = Id
ContentId = Id


@dataclass(slots=True)
class User: ...


@dataclass(slots=True)
class Content:
    data: bytes

    @property
    def id(self) -> ContentId:
        return sha3_512(self.data).hexdigest()


@dataclass(slots=True)
class Reference:
    file_path: Path
    content_id: ContentId

    @property
    def id(self) -> ReferenceId:
        return sha3_512(
            str(self.file_path).encode() + self.content_id.encode()
        ).hexdigest()


@dataclass(slots=True)
class Manifest:
    reference_ids: set[ReferenceId]

    @property
    def id(self) -> ManifestId:
        manifest_id = sha3_512()
        for reference_id in self.reference_ids:
            manifest_id.update(reference_id.encode())
        return manifest_id.hexdigest()


@dataclass(slots=True)
class Snapshot:
    manifest_id: ManifestId
    note: str | None

    @property
    def id(self) -> SnapshotId:
        snapshot_id = sha3_512()
        snapshot_id.update(self.manifest_id.encode())
        if self.note:
            snapshot_id.update(self.note.encode())
        return snapshot_id.hexdigest()


@dataclass(slots=True)
class Workspace:
    snapshot_ids: set[SnapshotId]
    id: WorkspaceId
