# Easysnapshot

### Goals

- **Many Archives:** Store in many archives at once.
- **Emergent Complexity:** Small implementation surface with reasonable usage requirements.

## Client

Clients gather and send information to archive endpoints.

### Commands

- All commands accept `--help` / `-h`.
- All commands accept `--verbose` / `-v`.
- **`ev archive register <archive:URL> [user:ID]`:** Claim a specific User ID on the given archive. User ID is random if omitted.
- **`ev archive unregister <archive:URL> <user:ID>`:** Requests the archive to forget this User ID.
- **`ev archive login <archive:URL> <user:ID> [workspace:PATH]`:** Sets this combination of Archive URL + User ID as active for this workspace.
- **`ev archive logout <archive:URL> <user:ID> [workspace:PATH]`:** Sets this combination of Archive URL + User ID as unactive for this workspace.
- **`ev save <--note <note:TEXT> | -n <note:TEXT> [workspace:PATH]`:** Save the workspace's current state as a new Snapshot, with the note when provided.
- **`ev list [workspace:PATH]`:** List the Workspace's Snapshots. Also showing notes where set.
- **`ev clone <source:PATH> <target:PATH> [--snapshot <snapshot:ID> | -s <snapshot:ID>]`:** Clone the source Workspace to the target path, which may not exist yet. Clone the current workspace state if omitted.
- **`ev forget {--snapshot <snapshot:ID> | -v <snapshot:ID> | --all | -a} [workspace:PATH]`:** Forget the specified snapshot(s) for the given Workspace.

## Archive

Clients recieve and save information from clients through their URL.

### Types

Five distinct types, forming one chain from workspace to content:

| Type        | Contents                                |
| ----------- | --------------------------------------- |
| `user`      | Metadata about the user account         |
| `workspace` | An array of snapshot hashes             |
| `snapshot`  | A manifest hash and an optional note    |
| `manifest`  | An array of reference hashes            |
| `reference` | A relative file path and a content hash |
| `content`   | Raw byte data                           |

### Endpoints

- **`HEAD /type/<type:ID>`:** Check whether the Type ID already exists.
- **`GET /type/<type:ID>`:** Returns an object with the Type's data.
- **`PUT /type/<type:ID>`:** Sets the object with the Type's data.
- **`DELETE /type/<type:ID>`:** Forget the given Type ID.

### Invariants

- All in workspace configuration, will be done under `./ev` in the workspace root.
- Archive URL + User ID login configurations are unique per workspace.
