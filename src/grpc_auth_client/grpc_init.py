from typing import Optional

from grpc import Channel

grpc_auth: Optional[Channel] = None


async def get_grpc():
    return grpc_auth
