import uuid
from collections.abc import AsyncGenerator  # noqa: TC003
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal, TypedDict

import uvicorn
from blake3 import blake3
from fastapi import Depends, FastAPI, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel

from evserver.stores import Archive
from evserver.types import (
    HASH_PATTERN,
    OBJECT_TYPES,
    USER_ID_PATTERN,
    Hash,
    ObjectType,
    UserId,
)


class State(TypedDict):
    archive: Archive


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[State]:
    yield State(archive=Archive(Path("data")))


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


def get_archive(request: Request) -> Archive:
    return request.state.archive


ArchiveDep = Annotated[Archive, Depends(get_archive)]


def validate_user_id(user_id: UserId) -> JSONResponse | None:
    if not USER_ID_PATTERN.fullmatch(user_id):
        return error("invalid_body", f'Invalid user id: "{user_id}".')
    return None


def validate_hash(obj_hash: Hash) -> JSONResponse | None:
    if not HASH_PATTERN.fullmatch(obj_hash):
        return error("invalid_hash", f'Invalid hash: "{obj_hash}".')
    return None


async def require_user(archive: Archive, user_id: UserId) -> JSONResponse | None:
    if not await archive.contains_user(user_id):
        return error("not_found", f'User: "{user_id}" does not exist.')
    return None


@app.post(
    "/user/register",
    response_model=None,
    status_code=201,
    response_class=PlainTextResponse,
)
async def register_user(archive: ArchiveDep) -> UserId:
    user_id = uuid.uuid4().hex
    await archive.add_user(user_id)
    return user_id


@app.post(
    "/user/register/{user_id}",
    response_model=None,
    status_code=201,
    response_class=PlainTextResponse,
)
async def claim_user(user_id: UserId, archive: ArchiveDep) -> UserId | JSONResponse:
    if err := validate_user_id(user_id):
        return err
    if await archive.contains_user(user_id):
        return error("conflict", f'User: "{user_id}" already exists.')
    await archive.add_user(user_id)
    return user_id


@app.delete("/user/{user_id}", response_model=None, response_class=PlainTextResponse)
async def delete_user(user_id: UserId, archive: ArchiveDep) -> UserId | JSONResponse:
    if err := await require_user(archive, user_id):
        return err
    await archive.delete_user(user_id)
    return user_id


@app.get("/user/{user_id}", response_model=None)
async def get_user(user_id: UserId, archive: ArchiveDep) -> list[Hash] | JSONResponse:
    if err := await require_user(archive, user_id):
        return err
    return await archive.hashes(user_id, "workspace")


def add_object_routes(obj_type: ObjectType) -> None:  # noqa: C901
    path = f"/user/{{user_id}}/{obj_type}/{{obj_hash}}"

    async def head_object(
        user_id: UserId, obj_hash: Hash, archive: ArchiveDep
    ) -> Response:
        if err := validate_hash(obj_hash):
            return err
        if err := await require_user(archive, user_id):
            return err
        if not await archive.contains(user_id, obj_type, obj_hash):
            return error("not_found", f'{obj_type}: "{obj_hash}" does not exist.')
        return Response(status_code=200)

    async def get_object(
        user_id: UserId, obj_hash: Hash, archive: ArchiveDep
    ) -> Response:
        if err := validate_hash(obj_hash):
            return err
        if err := await require_user(archive, user_id):
            return err
        if not await archive.contains(user_id, obj_type, obj_hash):
            return error("not_found", f'{obj_type}: "{obj_hash}" does not exist.')
        return Response(
            content=await archive.get(user_id, obj_type, obj_hash),
            media_type="application/octet-stream",
        )

    async def put_object(
        user_id: UserId, obj_hash: Hash, request: Request, archive: ArchiveDep
    ) -> Response:
        if err := validate_hash(obj_hash):
            return err
        if err := await require_user(archive, user_id):
            return err
        body = await request.body()
        if blake3(body).hexdigest() != obj_hash:
            return error("invalid_hash", "Body does not match the path hash.")
        if await archive.contains(user_id, obj_type, obj_hash):
            return PlainTextResponse(obj_hash, status_code=200)
        await archive.put(user_id, obj_type, obj_hash, body)
        return PlainTextResponse(obj_hash, status_code=201)

    async def delete_object(
        user_id: UserId, obj_hash: Hash, archive: ArchiveDep
    ) -> Response:
        if err := validate_hash(obj_hash):
            return err
        if err := await require_user(archive, user_id):
            return err
        if not await archive.contains(user_id, obj_type, obj_hash):
            return error("not_found", f'{obj_type}: "{obj_hash}" does not exist.')
        await archive.delete(user_id, obj_type, obj_hash)
        return PlainTextResponse(obj_hash)

    app.head(path, response_model=None)(head_object)
    app.get(path, response_model=None)(get_object)
    app.put(path, response_model=None, response_class=PlainTextResponse)(put_object)
    app.delete(path, response_model=None, response_class=PlainTextResponse)(
        delete_object
    )


for _obj_type in OBJECT_TYPES:
    add_object_routes(_obj_type)


def main() -> None:
    uvicorn.run("evserver:app", host="0.0.0.0", port=8000, workers=1)  # noqa: S104
