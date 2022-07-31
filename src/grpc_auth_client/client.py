from typing import Optional

from grpc_auth_client.protos import auth_pb2_grpc

channel = None

stub: Optional[auth_pb2_grpc.AuthStub] = None


async def get_stub() -> auth_pb2_grpc.AuthStub:
    return stub
