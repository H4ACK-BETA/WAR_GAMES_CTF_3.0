from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os


ADMIN_USERNAME = "cdn_admin"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "S3cur3_CDN_Adm1n_2024!")


class MetadataHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silent logging
        pass

    def do_GET(self):
        if self.path == "/":
            self._respond(200, {
                "service": "internal-metadata",
                "endpoints": ["/credentials", "/config", "/health"],
            })
        elif self.path == "/credentials":
            self._respond(200, {
                "admin_username": ADMIN_USERNAME,
                "admin_password": ADMIN_PASSWORD,
                "note": "CDN Admin Panel credentials",
            })
        elif self.path == "/config":
            self._respond(200, {
                "cdn_region": "ap-south-1",
                "storage_backend": "local",
                "imagemagick_version": "7.1.0",
            })
        elif self.path == "/health":
            self._respond(200, {"status": "healthy"})
        else:
            self._respond(404, {"error": "not found"})

    def _respond(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


def main():
    host = "127.0.0.1"
    port = 8888
    server = HTTPServer((host, port), MetadataHandler)
    print(f"[metadata] Listening on {host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
