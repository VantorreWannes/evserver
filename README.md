# evserver

HTTP archive server for EasyVersion objects.

## Scope

Stores and serves EasyVersion objects over HTTP.

Does not manage client workspaces, local configuration, or user registration workflows.

## Public API

Run the server with `evserver` (listens on `0.0.0.0:80`).

Each resource type (`user`, `workspace`, `snapshot`, `manifest`, `reference`, `content`) exposes four endpoints:

| Method   | Path            | Contract                                             |
| -------- | --------------- | ---------------------------------------------------- |
| `HEAD`   | `/{type}/{id}`  | Returns `200` if the ID exists, `404` otherwise.     |
| `GET`    | `/{type}/{id}`  | Returns the `dill`-serialized object, or `404`.      |
| `PUT`    | `/{type}/{id}`  | Stores the `dill`-serialized object from the body.   |
| `DELETE` | `/{type}/{id}`  | Deletes the object for the given ID if it exists.    |

## Ownership

- `evserver` is the single source of truth for persisted archive data under `data/` (`/app/data` in Docker).
- Clients own workspace state, ID generation, and object construction.

## Compatibility

- Request and response payloads use `dill`-serialized instances of `evserver.types` (`User`, `Workspace`, `Snapshot`, `Manifest`, `Reference`, `Content`).
- Changing type definitions or module paths in `evserver.types` breaks compatibility with existing stored data and clients.
