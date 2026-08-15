# EasyVersion (ev) | System Specification

**Document identifier:** EV-SPEC-001
**Status:** Draft
**Date:** 2026-08-15

---

## 1. Scope

This document specifies the requirements for **EasyVersion**, a version control system consisting of:

- a) a command-line client (`ev`), and
- b) an archive service accessed over HTTPS.

This document is intended for implementers of the client and the archive service. It does not cover installation, user tutorials, or administration.

## 2. Normative references

- **RFC 9110**, _HTTP Semantics_
- **BLAKE3** hash function specification

## 3. Terms and definitions

- **3.1 archive** | a remote service that stores blobs and workspace heads for users.
- **3.2 blob** | an immutable, content-addressed byte sequence.
- **3.3 workspace** | a directory under version control, identified by a `.ev` directory at its root.
- **3.4 head** | the single mutable hash an archive stores per workspace.
- **3.5 snapshot** | a blob identifying one version of a workspace.
- **3.6 version number** | a presentation-layer integer derived by the client; not stored or transmitted.

## 4. Conventions

The key words below are to be interpreted as follows:

| Keyword       | Interpretation                                           |
| ------------- | -------------------------------------------------------- |
| **shall**     | an absolute requirement                                  |
| **shall not** | an absolute prohibition                                  |
| **should**    | a recommendation; deviation permitted with justification |
| **may**       | a permitted option                                       |

## 5. Design principles

- **5.1 Scalar parameters.** Every parameter in the CLI and the API _shall_ be a scalar: one string, one integer, or one flag. No command or endpoint _shall_ accept a list, a pair, or a structured object as a parameter.
- **5.2 Opaque blobs.** Composite data _shall_ exist only inside blobs. The archive _shall not_ parse blob contents.
- **5.3 Content addressing.** Every blob _shall_ be identified by the BLAKE3 hash of its exact byte content.

## 6. Data types

Table 1 defines all scalar types used by this specification.

**Table 1 | Scalar types**

| Type     | Definition                                                                               |
| -------- | ---------------------------------------------------------------------------------------- |
| `UserId` | String, 1 to 64 chars, ASCII alphanumeric plus `-` and `_`                               |
| `Hash`   | String, lowercase hex BLAKE3 digest, exactly 64 chars                                    |
| `Url`    | String, valid HTTPS URL, no trailing slash, query, or fragment                           |
| `Path`   | String, filesystem path                                                                  |
| `Note`   | String, UTF-8, maximum 1024 chars                                                        |
| `Number` | Integer, greater than or equal to 1                                                      |
| `Bytes`  | Opaque byte sequence. Permitted only as a request or response body, never as a parameter |

## 7. Error handling

- **7.1** Every failure _shall_ be reported as two scalars: a `code` string and a `message` string.
- **7.2** The `code` _shall_ be one of: `not_found`, `conflict`, `invalid_hash`, `invalid_body`, `internal`.
- **7.3** HTTP status mapping _shall_ be:

| Code           | HTTP status |
| -------------- | ----------- |
| `not_found`    | 404         |
| `conflict`     | 409         |
| `invalid_hash` | 422         |
| `invalid_body` | 400         |
| `internal`     | 500         |

- **7.4** On internal error, the client _shall_ abort immediately and _shall not_ continue in a partially synced state.

## 8. Command-line interface

### 8.1 General requirements

- **8.1.1** All commands _shall_ accept `--help` or `-h`.
- **8.1.2** The workspace path argument _shall_ default to the current directory.
- **8.1.3** On success, output _shall_ consist of labeled scalars, one per line.
- **8.1.4** On failure, the client _shall_ print the error code and message to stderr and exit with a non-zero status.

### 8.2 Archive account commands

- **8.2.1** `ev archive <url> register`
  The client _shall_ request a server-chosen `UserId` and print `user_id`.
- **8.2.2** `ev archive <url> register <user_id>`
  The client _shall_ request the given `UserId` and print `user_id`. The command _shall_ fail with `conflict` if the `UserId` is taken.
- **8.2.3** `ev archive <url> unregister <user_id>`
  The client _shall_ request deletion of the user and all associated data, and print `user_id`.

### 8.3 Workspace configuration commands

- **8.3.1** `ev [path] login <url> <user_id>`
  The client _shall_ append one line `<url> <user_id>` to `.ev/archives`. The command _shall_ fail with `conflict` if that exact line exists.
- **8.3.2** `ev [path] logout <url> <user_id>`
  The client _shall_ remove that line. The command _shall_ fail with `not_found` if the line is absent.

### 8.4 Versioning commands

- **8.4.1** `ev [path] save`
  The client _shall_ snapshot the workspace, push to every configured archive, and print `version` and `hash`. The operation _shall_ fail atomically if any archive fails.
- **8.4.2** `ev [path] save -n <note>`
  As 8.4.1, with the note embedded in the snapshot.
- **8.4.3** `ev [path] list`
  The client _shall_ print one line per version: `number hash note`. The note field may be empty.
- **8.4.4** `ev [path] list <number>`
  The client _shall_ print the single matching line. The command _shall_ fail with `not_found` for an unknown number.
- **8.4.5** `ev clone <source_path> <target_path>`
  The client _shall_ clone the source workspace at its latest version. The command _shall_ fail if the target path exists.
- **8.4.6** `ev clone <source_path> <target_path> <number>`
  As 8.4.5, at the given version.
- **8.4.7** `ev [path] forget <number>`
  The client _shall_ remove the latest version from the archive head. Local files _shall_ remain untouched. The given number _shall_ equal the latest version number, else the command _shall_ fail with `conflict`.
- **8.4.8** `ev [path] forget --all`
  The client _shall_ remove all versions from the archive. Exactly one of `<number>` (8.4.7) or `--all` _shall_ be provided.

## 9. Archive API

### 9.1 General requirements

- **9.1.1** Every path parameter _shall_ be a scalar of type `UserId` or `Hash`.
- **9.1.2** Every request and response body _shall_ be one of: `Bytes`, a single scalar string, or a flat JSON array of scalar strings. No nested objects _shall_ cross the API boundary.

### 9.2 Account endpoints

- **9.2.1** `POST /user/register`
  Response `201`, body one `UserId` string.
- **9.2.2** `POST /user/register/<user_id>`
  Response `201`, body the `UserId`; or `conflict`.
- **9.2.3** `DELETE /user/<user_id>`
  Response `200`, body the `UserId`; or `not_found`. The archive _shall_ delete all of the user's blobs and workspaces.
- **9.2.4** `GET /user/<user_id>/workspaces`
  Response `200`, body a JSON array of `Hash` strings; or `not_found`.

### 9.3 Blob endpoints

- **9.3.1** `PUT /user/<user_id>/blob/<hash>` | body `Bytes`
  The archive _shall_ verify that `BLAKE3(body)` equals the path hash, else respond `invalid_hash`. Response `201`, body the `Hash`. Re-uploading identical bytes _shall_ return `200`.
- **9.3.2** `GET /user/<user_id>/blob/<hash>`
  Response `200`, body `Bytes`; or `not_found`.
- **9.3.3** `DELETE /user/<user_id>/blob/<hash>`
  Response `200`; or `not_found`; or `conflict` if any workspace head reaches the blob.

### 9.4 Workspace endpoints

A workspace on the archive _shall_ consist of a single mutable `Hash`: the head. History _shall not_ be stored by the archive.

- **9.4.1** `GET /user/<user_id>/workspace/<hash>`
  Response `200`, body one `Hash` string (the head); or `not_found`.
- **9.4.2** `PUT /user/<user_id>/workspace/<hash>` | body one `Hash` string
  The archive _shall_ verify the referenced blob exists, else respond `invalid_body`. Response `200`.
- **9.4.3** `DELETE /user/<user_id>/workspace/<hash>`
  Response `200`; or `not_found`.

### 9.5 Archive invariants

- **9.5.1** Blobs _shall_ be immutable.
- **9.5.2** Blob uploads _shall_ be idempotent.
- **9.5.3** A blob _shall_ be deleted only when no workspace head reaches it.
- **9.5.4** Archives _may_ garbage-collect unreachable blobs lazily.

## 10. Client requirements

### 10.1 Blob schemas

Blob schemas are client-side only and _shall_ never appear as API parameters. Each schema _shall_ be flat.

- **10.1.1 Content blob** | raw file bytes.
- **10.1.2 Manifest blob** | lines of `<content_hash> <relative_path>`, two scalars per line.
- **10.1.3 Snapshot blob** | three scalar fields: `manifest` (`Hash`), `parent` (`Hash`, empty for the first version), `note` (string, may be empty).

### 10.2 Version numbering

- **10.2.1** The hash of a snapshot blob _shall_ be the version's identity.
- **10.2.2** Version numbers _shall_ be derived by the client by walking the parent chain from the head; the oldest snapshot is version 1.

### 10.3 Configuration

- **10.3.1** All configuration _shall_ reside in `.ev/` at the workspace root.
- **10.3.2** `.ev/archives` _shall_ consist of lines of `<url> <user_id>`.

### 10.4 Save pipeline

- **10.4.1** `save` _shall_ execute one deterministic pipeline:
  1. hash file contents,
  2. write the manifest blob,
  3. write the snapshot blob with the current head as parent,
  4. push missing blobs to every archive,
  5. PUT the new head.

  The same pipeline _shall_ serve one or many archives.

### 10.5 Forget semantics

- **10.5.1** `forget <number>` _shall_ rewrite the head to that version's parent. Only the latest version may be forgotten individually.
- **10.5.2** Blob reclamation _shall_ be the archive's lazy garbage-collection concern (see 9.5.4).

---

## Annex A (informative) | Rationale

- **A.1** The mutable workspace state is one hash rather than a version list because linked history belongs in immutable, content-addressed blobs.
- **A.2** Version numbers are derived rather than stored to remove any possibility of disagreement between client and server.
- **A.3** Restricting `forget` to the latest version keeps the rule "history is immutable" absolute.
