"""GraphQL schema — exposes user queries and mutations."""
import strawberry
from strawberry.types import Info
from typing import Optional

from .models import get_user, update_user, users_db
from .auth import verify_token


@strawberry.type
class UserType:
    username: str
    role: str
    email: str
    bio: str


@strawberry.type
class ServiceInfo:
    """Internal service information — only visible to admins."""
    name: str
    protocol: str
    host: str
    port: int
    description: str


@strawberry.type
class MutationResponse:
    success: bool
    message: str
    user: Optional[UserType] = None


def get_current_user(info: Info) -> dict | None:
    """Extract user from request authorization header."""
    request = info.context["request"]
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        return verify_token(token)
    return None


@strawberry.type
class Query:
    @strawberry.field
    def me(self, info: Info) -> Optional[UserType]:
        """Get current user profile."""
        payload = get_current_user(info)
        if not payload:
            return None
        user = get_user(payload["sub"])
        if not user:
            return None
        return UserType(
            username=user.username,
            role=user.role,
            email=user.email,
            bio=user.bio,
        )

    @strawberry.field
    def user(self, info: Info, username: str) -> Optional[UserType]:
        """Look up a user by username."""
        payload = get_current_user(info)
        if not payload:
            return None
        user = get_user(username)
        if not user:
            return None
        return UserType(
            username=user.username,
            role=user.role,
            email=user.email,
            bio=user.bio,
        )

    @strawberry.field
    def internal_services(self, info: Info) -> list[ServiceInfo]:
        """
        List internal services.
        Should be admin-only but... introspection reveals it exists.
        """
        payload = get_current_user(info)
        if not payload or payload.get("role") != "admin":
            return []

        return [
            ServiceInfo(
                name="FlagService",
                protocol="gRPC",
                host="127.0.0.1",
                port=50051,
                description="Internal flag management service. Use gRPC reflection to discover methods.",
            ),
            ServiceInfo(
                name="MetricsService",
                protocol="REST",
                host="127.0.0.1",
                port=9090,
                description="Internal prometheus metrics.",
            ),
        ]


@strawberry.type
class Mutation:
    @strawberry.mutation
    def update_profile(
        self,
        info: Info,
        email: Optional[str] = None,
        bio: Optional[str] = None,
        role: Optional[str] = None,  # VULN: mass assignment!
    ) -> MutationResponse:
        """
        Update your profile.
        VULNERABILITY: The 'role' field is accepted and applied without validation.
        """
        payload = get_current_user(info)
        if not payload:
            return MutationResponse(success=False, message="Not authenticated")

        username = payload["sub"]
        update_fields = {}
        if email is not None:
            update_fields["email"] = email
        if bio is not None:
            update_fields["bio"] = bio
        if role is not None:
            # No authorization check — any user can set their own role!
            update_fields["role"] = role

        user = update_user(username, **update_fields)
        if not user:
            return MutationResponse(success=False, message="User not found")

        return MutationResponse(
            success=True,
            message="Profile updated",
            user=UserType(
                username=user.username,
                role=user.role,
                email=user.email,
                bio=user.bio,
            ),
        )


schema = strawberry.Schema(query=Query, mutation=Mutation)
