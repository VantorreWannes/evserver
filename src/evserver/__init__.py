from collections.abc import AsyncGenerator  # noqa: TC003
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, TypedDict

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
    user_id: UserId, user: User, user_store: UserStoreDependency
) -> None:
    await user_store.set(user_id, user)


@application.delete(
    "/user/{user_id}",
)
async def delete_user(user_id: UserId, user_store: UserStoreDependency) -> None:
    await user_store.delete(user_id)


def main() -> None:
    uvicorn.run("evserver:application")
