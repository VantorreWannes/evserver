import re
from typing import Literal

type UserId = str
type Hash = str
type ObjectType = Literal["workspace", "snapshot", "manifest", "reference", "content"]

OBJECT_TYPES: tuple[ObjectType, ...] = (
    "workspace",
    "snapshot",
    "manifest",
    "reference",
    "content",
)

USER_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")
