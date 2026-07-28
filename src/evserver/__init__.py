import uuid  # noqa: I001
from contextlib import asynccontextmanager
from http.client import HTTPException
from pathlib import Path
from typing import Annotated, TypedDict

from fastapi import Depends, FastAPI

from evserver.stores import DirectoryStore, FileStore, Store
from evserver.types import (
    Content,
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

from fastapi.requests import HTTPConnection  # noqa: TC002
from collections.abc import AsyncGenerator  # noqa: TC003


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


class State(TypedDict):
    user_store: UserStore
    workspace_store: WorkspaceStore
    snapshot_store: SnapshotStore
    manifest_store: ManifestStore
    reference_store: ReferenceStore
    content_store: ContentStore


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[State]:
    user_store = FileStore(Path("data/users.dill"))
    workspace_store = FileStore(Path("data/workspaces.dill"))
    snapshot_store = FileStore(Path("data/snapshots.dill"))
    manifest_store = FileStore(Path("data/manifests.dill"))
    reference_store = FileStore(Path("data/references.dill"))
    content_store = DirectoryStore(Path("data/contents"))
    yield State(
        user_store=user_store,
        workspace_store=workspace_store,
        snapshot_store=snapshot_store,
        manifest_store=manifest_store,
        reference_store=reference_store,
        content_store=content_store,
    )


app = FastAPI(lifespan=lifespan)


def get_user_store(httpconnection: HTTPConnection) -> UserStore:
    return httpconnection.state.user_store


def get_workspace_store(httpconnection: HTTPConnection) -> WorkspaceStore:
    return httpconnection.state.workspace_store


def get_snapshot_store(httpconnection: HTTPConnection) -> SnapshotStore:
    return httpconnection.state.snapshot_store


def get_manifest_store(httpconnection: HTTPConnection) -> ManifestStore:
    return httpconnection.state.manifest_store


def get_reference_store(httpconnection: HTTPConnection) -> ReferenceStore:
    return httpconnection.state.reference_store


def get_content_store(httpconnection: HTTPConnection) -> ContentStore:
    return httpconnection.state.content_store


@app.post("/user/register")
async def register_user(
    user_store: Annotated[UserStore, Depends(get_user_store)],
) -> User:
    user_id = uuid.uuid4().hex
    user = User(user_id, set())
    await user_store.set(user_id, user)
    return user


@app.post("/user/register/{user_id}")
async def claim_user(
    user_id: UserId,
    user_store: Annotated[UserStore, Depends(get_user_store)],
) -> None:
    if await user_store.contains(user_id):
        raise HTTPException(404, f'User: "{user_id}" already exists.')
    await user_store.set(user_id, User.from_id(user_id))


@app.delete("/user/{user_id}")
async def delete_user(
    user_id: UserId,
    user_store: Annotated[UserStore, Depends(get_user_store)],
) -> None:
    if not await user_store.contains(user_id):
        raise HTTPException(404, f'User: "{user_id}" does not exists.')
    await user_store.delete(user_id)


@app.get("/user/{user_id}")
async def get_user(
    user_id: UserId,
    user_store: Annotated[UserStore, Depends(get_user_store)],
) -> User:
    if not await user_store.contains(user_id):
        raise HTTPException(404, f'User: "{user_id}" does not exists.')
    return await user_store.get(user_id)


@app.get("/user/{user_id}/workspace/{workspace_id}")
async def get_workspace(
    user_id: UserId,
    workspace_id: WorkspaceId,
    workspace_store: Annotated[WorkspaceStore, Depends(get_workspace_store)],
) -> Workspace:
    workspace_key = (user_id, workspace_id)
    if not await workspace_store.contains(workspace_key):
        raise HTTPException(404, f'Workspace: "{workspace_key}" does not exists.')
    return await workspace_store.get(workspace_key)


@app.put("/user/{user_id}/workspace/{workspace_id}")
async def set_workspace(
    user_id: UserId,
    workspace_id: WorkspaceId,
    workspace: Workspace,
    workspace_store: Annotated[WorkspaceStore, Depends(get_workspace_store)],
) -> None:
    await workspace_store.set((user_id, workspace_id), workspace)


@app.delete("/user/{user_id}/workspace/{workspace_id}")
async def delete_workspace(
    user_id: UserId,
    workspace_id: WorkspaceId,
    workspace_store: Annotated[WorkspaceStore, Depends(get_workspace_store)],
) -> None:
    workspace_key = (user_id, workspace_id)
    if not await workspace_store.contains(workspace_key):
        raise HTTPException(404, f'Workspace: "{workspace_key}" does not exists.')
    await workspace_store.delete(workspace_key)


@app.get("/user/{user_id}/snapshot/{snapshot_id}")
async def get_snapshot(
    user_id: UserId,
    snapshot_id: SnapshotId,
    snapshot_store: Annotated[SnapshotStore, Depends(get_snapshot_store)],
) -> Snapshot:
    snapshot_key = (user_id, snapshot_id)
    if not await snapshot_store.contains(snapshot_key):
        raise HTTPException(404, f'Snapshot: "{snapshot_key}" does not exists.')
    return await snapshot_store.get(snapshot_key)


@app.put("/user/{user_id}/snapshot/{snapshot_id}")
async def set_snapshot(
    user_id: UserId,
    snapshot_id: SnapshotId,
    snapshot: Snapshot,
    snapshot_store: Annotated[SnapshotStore, Depends(get_snapshot_store)],
) -> None:
    await snapshot_store.set((user_id, snapshot_id), snapshot)


@app.delete("/user/{user_id}/snapshot/{snapshot_id}")
async def delete_snapshot(
    user_id: UserId,
    snapshot_id: SnapshotId,
    snapshot_store: Annotated[SnapshotStore, Depends(get_snapshot_store)],
) -> None:
    snapshot_key = (user_id, snapshot_id)
    if not await snapshot_store.contains(snapshot_key):
        raise HTTPException(404, f'Snapshot: "{snapshot_key}" does not exists.')
    await snapshot_store.delete(snapshot_key)


@app.get("/user/{user_id}/manifest/{manifest_id}")
async def get_manifest(
    user_id: UserId,
    manifest_id: ManifestId,
    manifest_store: Annotated[ManifestStore, Depends(get_manifest_store)],
) -> Manifest:
    manifest_key = (user_id, manifest_id)
    if not await manifest_store.contains(manifest_key):
        raise HTTPException(404, f'Manifest: "{manifest_key}" does not exists.')
    return await manifest_store.get(manifest_key)


@app.put("/user/{user_id}/manifest/{manifest_id}")
async def set_manifest(
    user_id: UserId,
    manifest_id: ManifestId,
    manifest: Manifest,
    manifest_store: Annotated[ManifestStore, Depends(get_manifest_store)],
) -> None:
    await manifest_store.set((user_id, manifest_id), manifest)


@app.delete("/user/{user_id}/manifest/{manifest_id}")
async def delete_manifest(
    user_id: UserId,
    manifest_id: ManifestId,
    manifest_store: Annotated[ManifestStore, Depends(get_manifest_store)],
) -> None:
    manifest_key = (user_id, manifest_id)
    if not await manifest_store.contains(manifest_key):
        raise HTTPException(404, f'Manifest: "{manifest_key}" does not exists.')
    await manifest_store.delete(manifest_key)


@app.get("/user/{user_id}/reference/{reference_id}")
async def get_reference(
    user_id: UserId,
    reference_id: ReferenceId,
    reference_store: Annotated[ReferenceStore, Depends(get_reference_store)],
) -> Reference:
    reference_key = (user_id, reference_id)
    if not await reference_store.contains(reference_key):
        raise HTTPException(404, f'Reference: "{reference_key}" does not exists.')
    return await reference_store.get(reference_key)


@app.put("/user/{user_id}/reference/{reference_id}")
async def set_reference(
    user_id: UserId,
    reference_id: ReferenceId,
    reference: Reference,
    reference_store: Annotated[ReferenceStore, Depends(get_reference_store)],
) -> None:
    await reference_store.set((user_id, reference_id), reference)


@app.delete("/user/{user_id}/reference/{reference_id}")
async def delete_reference(
    user_id: UserId,
    reference_id: ReferenceId,
    reference_store: Annotated[ManifestStore, Depends(get_reference_store)],
) -> None:
    manifest_key = (user_id, reference_id)
    if not await reference_store.contains(manifest_key):
        raise HTTPException(404, f'Reference: "{manifest_key}" does not exists.')
    await reference_store.delete(manifest_key)


@app.get("/user/{user_id}/content/{content_id}")
async def get_content(
    user_id: UserId,
    content_id: ContentId,
    content_store: Annotated[ContentStore, Depends(get_content_store)],
) -> Content:
    content_key = (user_id, content_id)
    if not await content_store.contains(content_key):
        raise HTTPException(404, f'Content: "{content_key}" does not exists.')
    return await content_store.get(content_key)


@app.put("/user/{user_id}/content/{content_id}")
async def set_content(
    user_id: UserId,
    content_id: ContentId,
    content: Content,
    content_store: Annotated[ContentStore, Depends(get_content_store)],
) -> None:
    await content_store.set((user_id, content_id), content)


@app.delete("/user/{user_id}/content/{content_id}")
async def delete_content(
    user_id: UserId,
    content_id: ContentId,
    content_store: Annotated[ManifestStore, Depends(get_content_store)],
) -> None:
    manifest_key = (user_id, content_id)
    if not await content_store.contains(manifest_key):
        raise HTTPException(404, f'Content: "{manifest_key}" does not exists.')
    await content_store.delete(manifest_key)
