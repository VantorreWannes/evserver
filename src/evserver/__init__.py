from collections.abc import AsyncGenerator  # noqa: TC003
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, TypedDict

import dill
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request

from evserver.stores import DirectoryStore
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


class State(TypedDict):
    user_store: DirectoryStore[UserId, User]
    workspace_store: DirectoryStore[WorkspaceId, Workspace]
    snapshot_store: DirectoryStore[SnapshotId, Snapshot]
    manifest_store: DirectoryStore[ManifestId, Manifest]
    reference_store: DirectoryStore[ReferenceId, Reference]
    content_store: DirectoryStore[ContentId, Content]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[State]:
    root_path = Path("data")
    user_store = DirectoryStore[UserId, User](root_path)
    workspace_store = DirectoryStore[WorkspaceId, Workspace](root_path)
    snapshot_store = DirectoryStore[SnapshotId, Snapshot](root_path)
    manifest_store = DirectoryStore[ManifestId, Manifest](root_path)
    reference_store = DirectoryStore[ReferenceId, Reference](root_path)
    content_store = DirectoryStore[ContentId, Content](root_path)
    yield State(
        user_store=user_store,
        workspace_store=workspace_store,
        snapshot_store=snapshot_store,
        manifest_store=manifest_store,
        reference_store=reference_store,
        content_store=content_store,
    )


application = FastAPI(lifespan=lifespan)


def get_user_store(request: Request) -> DirectoryStore[UserId, User]:
    return request.state.user_store


def get_workspace_store(request: Request) -> DirectoryStore[WorkspaceId, Workspace]:
    return request.state.workspace_store


def get_snapshot_store(request: Request) -> DirectoryStore[SnapshotId, Snapshot]:
    return request.state.snapshot_store


def get_manifest_store(request: Request) -> DirectoryStore[ManifestId, Manifest]:
    return request.state.manifest_store


def get_reference_store(request: Request) -> DirectoryStore[ReferenceId, Reference]:
    return request.state.reference_store


def get_content_store(request: Request) -> DirectoryStore[ContentId, Content]:
    return request.state.content_store


UserStoreDependency = Annotated[DirectoryStore[UserId, User], Depends(get_user_store)]
WorkspaceStoreDependency = Annotated[
    DirectoryStore[WorkspaceId, Workspace], Depends(get_workspace_store)
]
SnapshotDependency = Annotated[
    DirectoryStore[SnapshotId, Snapshot], Depends(get_snapshot_store)
]
ManifestStoreDependency = Annotated[
    DirectoryStore[ManifestId, Manifest], Depends(get_manifest_store)
]
ReferenceStoreDependency = Annotated[
    DirectoryStore[ReferenceId, Reference], Depends(get_reference_store)
]
ContentStoreDependency = Annotated[
    DirectoryStore[ContentId, Content], Depends(get_content_store)
]


@application.head(
    "/user/{user_id}",
)
async def head_user(user_id: UserId, user_store: UserStoreDependency) -> None:
    if not await user_store.contains(user_id):
        raise HTTPException(404)


@application.get(
    "/user/{user_id}",
)
async def get_user(user_id: UserId, user_store: UserStoreDependency) -> User:
    if await user_store.contains(user_id):
        return await user_store.get(user_id)
    raise HTTPException(404)


@application.put(
    "/user/{user_id}",
)
async def put_user(
    user_id: UserId, request: Request, user_store: UserStoreDependency
) -> None:
    user: User = dill.loads(await request.body())  # noqa: S301
    await user_store.set(user_id, user)


@application.delete(
    "/user/{user_id}",
)
async def delete_user(user_id: UserId, user_store: UserStoreDependency) -> None:
    if user_store.contains(user_id):
        await user_store.delete(user_id)


@application.head(
    "/workspace/{workspace_id}",
)
async def head_workspace(
    workspace_id: WorkspaceId, workspace_store: WorkspaceStoreDependency
) -> None:
    if not await workspace_store.contains(workspace_id):
        raise HTTPException(404)


@application.get(
    "/workspace/{workspace_id}",
)
async def get_workspace(
    workspace_id: WorkspaceId, workspace_store: WorkspaceStoreDependency
) -> Workspace:
    if await workspace_store.contains(workspace_id):
        return await workspace_store.get(workspace_id)
    raise HTTPException(404)


@application.put(
    "/workspace/{workspace_id}",
)
async def put_workspace(
    workspace_id: WorkspaceId,
    request: Request,
    workspace_store: WorkspaceStoreDependency,
) -> None:
    workspace: Workspace = dill.loads(await request.body())  # noqa: S301
    await workspace_store.set(workspace_id, workspace)


@application.delete(
    "/workspace/{workspace_id}",
)
async def delete_workspace(
    workspace_id: WorkspaceId, workspace_store: WorkspaceStoreDependency
) -> None:
    if workspace_store.contains(workspace_id):
        await workspace_store.delete(workspace_id)


@application.head(
    "/snapshot/{snapshot_id}",
)
async def head_snapshot(
    snapshot_id: SnapshotId, snapshot_store: SnapshotDependency
) -> None:
    if not await snapshot_store.contains(snapshot_id):
        raise HTTPException(404)


@application.get(
    "/snapshot/{snapshot_id}",
)
async def get_snapshot(
    snapshot_id: SnapshotId, snapshot_store: SnapshotDependency
) -> Snapshot:
    if await snapshot_store.contains(snapshot_id):
        return await snapshot_store.get(snapshot_id)
    raise HTTPException(404)


@application.put(
    "/snapshot/{snapshot_id}",
)
async def put_snapshot(
    snapshot_id: SnapshotId,
    request: Request,
    snapshot_store: SnapshotDependency,
) -> None:
    snapshot: Snapshot = dill.loads(await request.body())  # noqa: S301
    await snapshot_store.set(snapshot_id, snapshot)


@application.delete(
    "/snapshot/{snapshot_id}",
)
async def delete_snapshot(
    snapshot_id: SnapshotId, snapshot_store: SnapshotDependency
) -> None:
    if snapshot_store.contains(snapshot_id):
        await snapshot_store.delete(snapshot_id)


@application.head(
    "/manifest/{manifest_id}",
)
async def head_manifest(
    manifest_id: ManifestId, manifest_store: ManifestStoreDependency
) -> None:
    if not await manifest_store.contains(manifest_id):
        raise HTTPException(404)


@application.get(
    "/manifest/{manifest_id}",
)
async def get_manifest(
    manifest_id: ManifestId, manifest_store: ManifestStoreDependency
) -> Manifest:
    if await manifest_store.contains(manifest_id):
        return await manifest_store.get(manifest_id)
    raise HTTPException(404)


@application.put(
    "/manifest/{manifest_id}",
)
async def put_manifest(
    manifest_id: ManifestId,
    request: Request,
    manifest_store: ManifestStoreDependency,
) -> None:
    manifest: Manifest = dill.loads(await request.body())  # noqa: S301
    await manifest_store.set(manifest_id, manifest)


@application.delete(
    "/manifest/{manifest_id}",
)
async def delete_manifest(
    manifest_id: ManifestId, manifest_store: ManifestStoreDependency
) -> None:
    if manifest_store.contains(manifest_id):
        await manifest_store.delete(manifest_id)


@application.head(
    "/reference/{reference_id}",
)
async def head_reference(
    reference_id: ReferenceId, reference_store: ReferenceStoreDependency
) -> None:
    if not await reference_store.contains(reference_id):
        raise HTTPException(404)


@application.get(
    "/reference/{reference_id}",
)
async def get_reference(
    reference_id: ReferenceId, reference_store: ReferenceStoreDependency
) -> Reference:
    if await reference_store.contains(reference_id):
        return await reference_store.get(reference_id)
    raise HTTPException(404)


@application.put(
    "/reference/{reference_id}",
)
async def put_reference(
    reference_id: ReferenceId,
    request: Request,
    reference_store: ReferenceStoreDependency,
) -> None:
    reference: Reference = dill.loads(await request.body())  # noqa: S301
    await reference_store.set(reference_id, reference)


@application.delete(
    "/reference/{reference_id}",
)
async def delete_reference(
    reference_id: ReferenceId, reference_store: ReferenceStoreDependency
) -> None:
    if reference_store.contains(reference_id):
        await reference_store.delete(reference_id)


@application.head(
    "/content/{content_id}",
)
async def head_content(
    content_id: ContentId, content_store: ContentStoreDependency
) -> None:
    if not await content_store.contains(content_id):
        raise HTTPException(404)


@application.get(
    "/content/{content_id}",
)
async def get_content(
    content_id: ContentId, content_store: ContentStoreDependency
) -> Content:
    if await content_store.contains(content_id):
        return await content_store.get(content_id)
    raise HTTPException(404)


@application.put(
    "/content/{content_id}",
)
async def put_content(
    content_id: ContentId,
    request: Request,
    content_store: ContentStoreDependency,
) -> None:
    content: Content = dill.loads(await request.body())  # noqa: S301
    await content_store.set(content_id, content)


@application.delete(
    "/content/{content_id}",
)
async def delete_content(
    content_id: ContentId, content_store: ContentStoreDependency
) -> None:
    if content_store.contains(content_id):
        await content_store.delete(content_id)


def main() -> None:
    uvicorn.run("evserver:application")
