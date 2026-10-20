from typing import NewType
from uuid import uuid4

PartnerId = NewType("PartnerId", str)
ChannelId = NewType("ChannelId", str)
VideoId = NewType("VideoId", str)
SyncRunId = NewType("SyncRunId", str)
UserId = NewType("UserId", str)


def new_id() -> str:
    return uuid4().hex
