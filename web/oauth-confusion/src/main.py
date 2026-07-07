"""
Main entry point — runs both the OAuth Authorization Server and Client App.
Uses threading to serve both on different ports in a single container.
"""
import threading
from .auth_server import create_auth_app
from .client_app import create_client_app
from .config import AUTH_SERVER_PORT, CLIENT_APP_PORT


def run_auth_server():
    """Run the authorization server."""
    app = create_auth_app()
    app.run(host="0.0.0.0", port=AUTH_SERVER_PORT, debug=False, use_reloader=False)


def run_client_app():
    """Run the client application."""
    app = create_client_app()
    app.run(host="0.0.0.0", port=CLIENT_APP_PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    print(f"[*] Starting OAuth Authorization Server on port {AUTH_SERVER_PORT}")
    print(f"[*] Starting Client Application on port {CLIENT_APP_PORT}")
    print()

    auth_thread = threading.Thread(target=run_auth_server, daemon=True)
    auth_thread.start()

    # Run client app in main thread
    run_client_app()
