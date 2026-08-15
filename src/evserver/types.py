import re

type UserId = str
type Hash = str

USER_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")
