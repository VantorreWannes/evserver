import uuid
from collections.abc import AsyncGenerator  # noqa: TC003
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal, TypedDict

import uvicorn
from blake3 import blake3
from fastapi import Body, Depends, FastAPI, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel

from evserver.stores import BlobStore, FileStore
from evserver.types import HASH_PATTERN, USER_ID_PATTERN, Hash, UserId

UserStore = FileStore[UserId, None]
WorkspaceStore = FileStore[tuple[UserId, Hash], Hash]


class State(TypedDict):
    user_store: UserStore
    workspace_store: WorkspaceStore
    blob_store: BlobStore


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[State]:
    yield State(
        user_store=FileStore(Path("data/users.dill")),
        workspace_store=FileStore(Path("data/workspaces.dill")),
        blob_store=BlobStore(Path("data/blobs")),
    )


app = FastAPI(lifespan=lifespan)

ErrorCode = Literal["not_found", "conflict", "invalid_hash", "invalid_body", "internal"]

ERROR_STATUS: dict[ErrorCode, int] = {
    "not_found": 404,
    "conflict": 409,
    "invalid_hash": 422,
    "invalid_body": 400,
    "internal": 500,
}


class ErrorBody(BaseModel):
    code: ErrorCode
    message: str


def error(code: ErrorCode, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=ERROR_STATUS[code],
        content=ErrorBody(code=code, message=message).model_dump(),
    )


def get_user_store(request: Request) -> UserStore:
    return request.state.user_store


def get_workspace_store(request: Request) -> WorkspaceStore:
    return request.state.workspace_store


def get_blob_store(request: Request) -> BlobStore:
    return request.state.blob_store


UserStoreDep = Annotated[UserStore, Depends(get_user_store)]
WorkspaceStoreDep = Annotated[WorkspaceStore, Depends(get_workspace_store)]
BlobStoreDep = Annotated[BlobStore, Depends(get_blob_store)]


def validate_user_id(user_id: UserId) -> JSONResponse | None:
    if not USER_ID_PATTERN.fullmatch(user_id):
        return error("invalid_body", f'Invalid user id: "{user_id}".')
    return None


def validate_hash(blob_hash: Hash) -> JSONResponse | None:
    if not HASH_PATTERN.fullmatch(blob_hash):
        return error("invalid_hash", f'Invalid hash: "{blob_hash}".')
    return None


async def require_user(user_store: UserStore, user_id: UserId) -> JSONResponse | None:
    if not await user_store.contains(user_id):
        return error("not_found", f'User: "{user_id}" does not exist.')
    return None


@app.post(
    "/user/register",
    response_model=None,
    status_code=201,
    response_class=PlainTextResponse,
)
async def register_user(user_store: UserStoreDep) -> UserId:
    user_id = uuid.uuid4().hex
    await user_store.set(user_id, None)
    return user_id


@app.post(
    "/user/register/{user_id}",
    response_model=None,
    status_code=201,
    response_class=PlainTextResponse,
)
async def claim_user(
    user_id: UserId, user_store: UserStoreDep
) -> UserId | JSONResponse:
    if err := validate_user_id(user_id):
        return err
    if await user_store.contains(user_id):
        return error("conflict", f'User: "{user_id}" already exists.')
    await user_store.set(user_id, None)
    return user_id


@app.delete("/user/{user_id}", response_model=None, response_class=PlainTextResponse)
async def delete_user(
    user_id: UserId,
    user_store: UserStoreDep,
    workspace_store: WorkspaceStoreDep,
    blob_store: BlobStoreDep,
) -> UserId | JSONResponse:
    if err := await require_user(user_store, user_id):
        return err
    for key in await workspace_store.keys():
        if key[0] == user_id:
            await workspace_store.delete(key)
    await blob_store.delete_user(user_id)
    await user_store.delete(user_id)
    return user_id


@app.get("/user/{user_id}/workspaces", response_model=None)
async def get_workspaces(
    user_id: UserId,
    user_store: UserStoreDep,
    workspace_store: WorkspaceStoreDep,
) -> list[Hash] | JSONResponse:
    if err := await require_user(user_store, user_id):
        return err
    return [
        workspace_id
        for uid, workspace_id in await workspace_store.keys()
        if uid == user_id
    ]


@app.put(
    "/user/{user_id}/blob/{blob_hash}",
    response_model=None,
    response_class=PlainTextResponse,
)
async def put_blob(
    user_id: UserId,
    blob_hash: Hash,
    request: Request,
    user_store: UserStoreDep,
    blob_store: BlobStoreDep,
) -> Response:
    if err := validate_hash(blob_hash):
        return err
    if err := await require_user(user_store, user_id):
        return err
    body = await request.body()
    if blake3(body).hexdigest() != blob_hash:
        return error("invalid_hash", "Body does not match the path hash.")
    if await blob_store.contains(user_id, blob_hash):
        return PlainTextResponse(blob_hash, status_code=200)
    await blob_store.set(user_id, blob_hash, body)
    return PlainTextResponse(blob_hash, status_code=201)


@app.get("/user/{user_id}/blob/{blob_hash}", response_model=None)
async def get_blob(
    user_id: UserId,
    blob_hash: Hash,
    user_store: UserStoreDep,
    blob_store: BlobStoreDep,
) -> Response:
    if err := validate_hash(blob_hash):
        return err
    if err := await require_user(user_store, user_id):
        return err
    if not await blob_store.contains(user_id, blob_hash):
        return error("not_found", f'Blob: "{blob_hash}" does not exist.')
    return Response(
        content=await blob_store.get(user_id, blob_hash),
        media_type="application/octet-stream",
    )


@app.delete(
    "/user/{user_id}/blob/{blob_hash}",
    response_model=None,
    response_class=PlainTextResponse,
)
async def delete_blob(
    user_id: UserId,
    blob_hash: Hash,
    user_store: UserStoreDep,
    workspace_store: WorkspaceStoreDep,
    blob_store: BlobStoreDep,
) -> Response:
    if err := validate_hash(blob_hash):
        return err
    if err := await require_user(user_store, user_id):
        return err
    if not await blob_store.contains(user_id, blob_hash):
        return error("not_found", f'Blob: "{blob_hash}" does not exist.')
    heads = [
        await workspace_store.get(k)
        for k in await workspace_store.keys()
        if k[0] == user_id
    ]
    if blob_hash in heads:
        return error(
            "conflict", f'Blob: "{blob_hash}" is referenced by a workspace head.'
        )
    await blob_store.delete(user_id, blob_hash)
    return PlainTextResponse(blob_hash)


@app.get(
    "/user/{user_id}/workspace/{workspace_hash}",
    response_model=None,
    response_class=PlainTextResponse,
)
async def get_workspace(
    user_id: UserId,
    workspace_hash: Hash,
    user_store: UserStoreDep,
    workspace_store: WorkspaceStoreDep,
) -> Hash | JSONResponse:
    if err := validate_hash(workspace_hash):
        return err
    if err := await require_user(user_store, user_id):
        return err
    key = (user_id, workspace_hash)
    if not await workspace_store.contains(key):
        return error("not_found", f'Workspace: "{workspace_hash}" does not exist.')
    return await workspace_store.get(key)


@app.put(
    "/user/{user_id}/workspace/{workspace_hash}",
    response_model=None,
    response_class=PlainTextResponse,
)
async def put_workspace(  # noqa: PLR0913, PLR0917
    user_id: UserId,
    workspace_hash: Hash,
    head: Annotated[str, Body(media_type="text/plain")],
    user_store: UserStoreDep,
    workspace_store: WorkspaceStoreDep,
    blob_store: BlobStoreDep,
) -> Response:
    if err := validate_hash(workspace_hash):
        return err
    if err := await require_user(user_store, user_id):
        return err
    if err := validate_hash(head):
        return error("invalid_body", f'Invalid head hash: "{head}".')
    if not await blob_store.contains(user_id, head):
        return error("invalid_body", f'Head blob: "{head}" does not exist.')
    await workspace_store.set((user_id, workspace_hash), head)
    return PlainTextResponse(workspace_hash)


@app.delete(
    "/user/{user_id}/workspace/{workspace_hash}",
    response_model=None,
    response_class=PlainTextResponse,
)
async def delete_workspace(
    user_id: UserId,
    workspace_hash: Hash,
    user_store: UserStoreDep,
    workspace_store: WorkspaceStoreDep,
) -> Hash | JSONResponse:
    if err := validate_hash(workspace_hash):
        return err
    if err := await require_user(user_store, user_id):
        return err
    key = (user_id, workspace_hash)
    if not await workspace_store.contains(key):
        return error("not_found", f'Workspace: "{workspace_hash}" does not exist.')
    await workspace_store.delete(key)
    return workspace_hash


def main() -> None:
    uvicorn.run("evserver:app")
