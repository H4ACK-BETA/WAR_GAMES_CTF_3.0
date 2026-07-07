"""gRPC Flag Service — internal service that returns the flag to admins."""
import grpc
from concurrent import futures
import os
import sys

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.proto import flag_pb2, flag_pb2_grpc
from src.auth import verify_token
from grpc_reflection.v1alpha import reflection


def read_flag() -> str:
    """Read flag from /flag file or GZCTF_FLAG/FLAG env var."""
    # Try env vars first (GZCTF dynamic challenge)
    flag = os.environ.get("GZCTF_FLAG") or os.environ.get("FLAG")
    if flag:
        return flag.strip()

    # Fallback to /flag file
    try:
        with open("/flag", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        pass

    # Dev fallback
    try:
        flag_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "flag.txt")
        with open(flag_path, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "WarCTF{flag_not_configured}"


class FlagServiceServicer(flag_pb2_grpc.FlagServiceServicer):
    """gRPC service that serves the flag to authenticated admins."""

    def GetFlag(self, request, context):
        """Return the flag if the token belongs to an admin."""
        token = request.token

        # Also check metadata for token
        if not token:
            metadata = dict(context.invocation_metadata())
            token = metadata.get("authorization", "").replace("Bearer ", "")

        if not token:
            return flag_pb2.FlagResponse(
                flag="",
                message="Access denied: no token provided. Include your JWT token in the request.",
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
        return flag_pb2.FlagResponse(
            flag=flag,
            message="Congratulations! You've chained all three APIs!",
        )

    def Ping(self, request, context):
        """Health check."""
        return flag_pb2.PingResponse(status="FlagService is running")


def serve(port: int = 50051):
    """Start the gRPC server with reflection enabled."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    flag_pb2_grpc.add_FlagServiceServicer_to_server(FlagServiceServicer(), server)

    # Enable reflection so players can discover the service
    SERVICE_NAMES = (
        flag_pb2.DESCRIPTOR.services_by_name["FlagService"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)

    server.add_insecure_port(f"0.0.0.0:{port}")
    print(f"[gRPC] FlagService listening on port {port} (reflection enabled)")
    server.start()
    return server


if __name__ == "__main__":
    server = serve()
    server.wait_for_termination()
