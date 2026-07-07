# API Playground - Web Challenge (Hard)

Multi-protocol API exploitation: REST → GraphQL → gRPC chain.

## Quick Start (Local Testing)

```bash
docker-compose up --build
```

Or without Docker:
```bash
pip install -r requirements.txt
bash gen_proto.sh
FLAG="WarCTF{test_flag}" python -m uvicorn src.main:app --host 0.0.0.0 --port 8080
```

## GZCTF Deployment

- **Type:** Dynamic container
- **Ports:** 8080 (HTTP), 50051 (gRPC)
- **Flag:** Set via `GZCTF_FLAG` or `FLAG` env var
- **Image:** Build from Dockerfile

## Attack Flow

1. Register via REST `/api/v1/auth/register`
2. Discover hidden `/api/v1/internal/services`
3. GraphQL introspection reveals `updateProfile(role: ...)` mutation
4. Mass assignment: set role to "admin"
5. As admin, query `internalServices` in GraphQL for gRPC details
6. Call `FlagService.GetFlag` via gRPC with admin JWT → flag

## Solve

```bash
python solve.py <host> <http_port> <grpc_port>
```
