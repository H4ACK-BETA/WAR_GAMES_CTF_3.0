"""
API Playground — Multi-protocol CTF Challenge
Serves REST + GraphQL on HTTP, with a gRPC backend.
"""
import os
import threading

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import strawberry
from strawberry.fastapi import GraphQLRouter

from .auth import create_token, verify_token, get_role_from_token
from .models import create_user, authenticate_user, get_user, users_db
from .graphql_schema import schema
from .grpc_server import serve as grpc_serve

# --- App Setup ---
app = FastAPI(
    title="API Playground",
    description="Multi-protocol API platform",
    version="1.0.0",
    docs_url=None,  # Hide default docs
    redoc_url=None,
)

# --- Mount GraphQL ---
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")


# --- Pydantic Models ---
class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = ""


class LoginRequest(BaseModel):
    username: str
    password: str


# --- Auth dependency ---
def get_current_payload(authorization: Optional[str] = Header(None)) -> dict:
    """Extract and verify JWT from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization[7:]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


# --- Public REST Endpoints ---
@app.get("/")
def root():
    return {
        "service": "API Playground",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/v1/auth",
            "docs": "/api/v1/docs",
        },
        "message": "Welcome to the API Playground! Check /api/v1/docs for available endpoints.",
    }


@app.get("/api/v1/docs")
def docs():
    """Public API documentation — intentionally incomplete."""
    return {
        "endpoints": [
            {"method": "POST", "path": "/api/v1/auth/register", "description": "Register a new account"},
            {"method": "POST", "path": "/api/v1/auth/login", "description": "Login and receive JWT token"},
            {"method": "GET", "path": "/api/v1/profile", "description": "Get your profile (auth required)"},
            {"method": "GET", "path": "/api/v1/health", "description": "Service health check"},
        ],
        "note": "All authenticated endpoints require: Authorization: Bearer <token>",
    }


@app.post("/api/v1/auth/register")
def register(req: RegisterRequest):
    if len(req.username) < 3 or len(req.password) < 4:
        raise HTTPException(status_code=400, detail="Username (min 3) and password (min 4) required")
    user = create_user(req.username, req.password, req.email or "")
    if not user:
        raise HTTPException(status_code=409, detail="Username already taken")
    token = create_token(user.username, user.role)
    return {"message": "Registration successful", "token": token, "role": user.role}


@app.post("/api/v1/auth/login")
def login(req: LoginRequest):
    user = authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user.username, user.role)
    return {"message": "Login successful", "token": token, "role": user.role}


@app.get("/api/v1/profile")
def profile(payload: dict = Depends(get_current_payload)):
    user = get_user(payload["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "username": user.username,
        "role": user.role,
        "email": user.email,
        "bio": user.bio,
    }


@app.get("/api/v1/health")
def health():
    return {"status": "healthy", "services": ["rest", "graphql"]}


# --- Hidden / Internal Endpoints ---
# These are not in /api/v1/docs but discoverable via fuzzing or error messages

@app.get("/api/v1/internal/services")
def internal_services(payload: dict = Depends(get_current_payload)):
    """
    Hidden endpoint — lists internal services.
    Accessible to any authenticated user (information disclosure).
    Hints at GraphQL and gRPC existence.
    """
    return {
        "services": [
            {
                "name": "GraphQL API",
                "endpoint": "/graphql",
                "description": "Advanced query interface. Supports introspection.",
                "note": "Use your JWT token in Authorization header",
            },
            {
                "name": "FlagService (gRPC)",
                "host": "127.0.0.1",
                "port": 50051,
                "description": "Internal microservice. Admin access required.",
                "note": "gRPC reflection is enabled for service discovery.",
            },
        ],
        "hint": "Some services support protocol-specific discovery mechanisms...",
    }


@app.get("/api/v1/internal/debug")
def debug_info(payload: dict = Depends(get_current_payload)):
    """Another hidden endpoint — leaks useful debug info."""
    return {
        "environment": "development",
        "user_count": len(users_db),
        "your_role": payload.get("role"),
        "jwt_algorithm": "HS256",
        "grpc_reflection": True,
        "note": "GraphQL mutations accept more fields than documented...",
    }


# --- gRPC startup in background thread ---
@app.on_event("startup")
def start_grpc():
    """Launch gRPC server in a background thread."""
    thread = threading.Thread(target=_run_grpc, daemon=True)
    thread.start()


def _run_grpc():
    server = grpc_serve(port=50051)
    server.wait_for_termination()
