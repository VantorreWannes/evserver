from starlette.responses import Content

from evserver.stores import Store
from evserver.types import (
    ContentId,
    Manifest,
    ManifestId,
    Reference,
    ReferenceId,
    Snapshot,
    SnapshotId,
    User,
    UserId,
    Workspace,
    WorkspaceId,
)

UserKey = UserId
WorkspaceKey = tuple[UserId, WorkspaceId]
SnapshotKey = tuple[UserId, SnapshotId]
ManifestKey = tuple[UserId, ManifestId]
ReferenceKey = tuple[UserId, ReferenceId]
ContentKey = tuple[UserId, ContentId]


UserStore = Store[UserId, User]
WorkspaceStore = Store[WorkspaceKey, Workspace]
SnapshotStore = Store[SnapshotKey, Snapshot]
ManifestStore = Store[ManifestKey, Manifest]
ReferenceStore = Store[ReferenceKey, Reference]
ContentStore = Store[ContentKey, Content]
