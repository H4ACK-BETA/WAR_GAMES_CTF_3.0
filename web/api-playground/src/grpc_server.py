"""gRPC Flag Service."""
import grpc
from concurrent import futures
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.proto import flag_pb2, flag_pb2_grpc
from src.auth import verify_token
from grpc_reflection.v1alpha import reflection


def read_flag() -> str:
    flag = os.environ.get("GZCTF_FLAG") or os.environ.get("FLAG")
    if flag:
        return flag.strip()
    try:
        with open("/flag", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        pass
    try:
        flag_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "flag.txt")
        with open(flag_path, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "WarCTF{flag_not_configured}"


class FlagServiceServicer(flag_pb2_grpc.FlagServiceServicer):

    def GetFlag(self, request, context):
        token = request.token
        if not token:
            metadata = dict(context.invocation_metadata())
            token = metadata.get("authorization", "").replace("Bearer ", "")

        if not token:
            return flag_pb2.FlagResponse(
                flag="",
                message="Access denied: no token provided.",
            )

        payload = verify_token(token)
        if not payload:
            return flag_pb2.FlagResponse(
                flag="",
                message="Access denied: invalid or expired token.",
            )

        if payload.get("role") != "admin":
            return flag_pb2.FlagResponse(
                flag="",
                message=f"Access denied: role '{payload.get('role')}' insufficient. Admin required.",
            )

        flag = read_flag()
        return flag_pb2.FlagResponse(flag=flag, message="Congratulations!")

    def Ping(self, request, context):
        return flag_pb2.PingResponse(status="FlagService is running")


def serve(port: int = 50051):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    flag_pb2_grpc.add_FlagServiceServicer_to_server(FlagServiceServicer(), server)

    SERVICE_NAMES = (
        flag_pb2.DESCRIPTOR.services_by_name["FlagService"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)

    server.add_insecure_port(f"0.0.0.0:{port}")
    print(f"[gRPC] FlagService listening on port {port}")
    server.start()
    return server


if __name__ == "__main__":
    server = serve()
    server.wait_for_termination()
