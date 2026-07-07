"""Simulated Kubernetes API Server for CTF challenge."""
import json
import base64
import os
import hashlib
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl

SERVICE_ACCOUNT_TOKEN = None
BACKUP_TOKEN = None
FLAG = None


def init_tokens():
    global SERVICE_ACCOUNT_TOKEN, BACKUP_TOKEN, FLAG

    FLAG = os.environ.get("GZCTF_FLAG") or os.environ.get("FLAG")
    if not FLAG:
        try:
            with open("/flag", "r") as f:
                FLAG = f.read().strip()
        except FileNotFoundError:
            FLAG = "WarCTF{kub3_s3cr3ts_4r3nt_encrypt3d_p1v0t_ftw}"

    seed = os.environ.get("TOKEN_SEED", "novacorp-prod")
    SERVICE_ACCOUNT_TOKEN = "eyJhbGciOiJSUzI1NiJ9." + base64.urlsafe_b64encode(
        json.dumps({"sub": "system:serviceaccount:production:frontend-sa", "iss": "kubernetes/serviceaccount"}).encode()
    ).decode().rstrip("=") + ".k8s_sig_" + hashlib.md5(seed.encode()).hexdigest()[:16]

    BACKUP_TOKEN = "eyJhbGciOiJSUzI1NiJ9." + base64.urlsafe_b64encode(
        json.dumps({"sub": "system:serviceaccount:production:backup-agent-sa", "iss": "kubernetes/serviceaccount"}).encode()
    ).decode().rstrip("=") + ".k8s_sig_" + hashlib.md5((seed + "backup").encode()).hexdigest()[:16]


PODS_DATA = {
    "kind": "PodList",
    "apiVersion": "v1",
    "items": [
        {
            "metadata": {"name": "frontend-7b9d4f8c6-x2k4m", "namespace": "production",
                         "labels": {"app": "frontend", "tier": "web"}},
            "spec": {"serviceAccountName": "frontend-sa",
                     "containers": [{"name": "flask-app", "image": "novacorp/frontend:2.1.3"}]},
            "status": {"phase": "Running", "podIP": "10.244.0.12"},
        },
        {
            "metadata": {"name": "backend-api-5c8f7d9b2-j8n3p", "namespace": "production",
                         "labels": {"app": "backend", "tier": "api"}},
            "spec": {"serviceAccountName": "default",
                     "containers": [{"name": "node-api", "image": "novacorp/backend:1.8.0"}]},
            "status": {"phase": "Running", "podIP": "10.244.0.14"},
        },
        {
            "metadata": {"name": "payments-6d4e8a1c9-w5r2t", "namespace": "production",
                         "labels": {"app": "payments", "tier": "service"}},
            "spec": {"serviceAccountName": "default",
                     "containers": [{"name": "payment-processor", "image": "novacorp/payments:3.0.1"}]},
            "status": {"phase": "Running", "podIP": "10.244.0.16"},
        },
        {
            "metadata": {"name": "redis-master-0", "namespace": "production",
                         "labels": {"app": "redis", "tier": "cache"}},
            "spec": {"serviceAccountName": "default",
                     "containers": [{"name": "redis", "image": "redis:7-alpine"}]},
            "status": {"phase": "Running", "podIP": "10.244.0.18"},
        },
        {
            "metadata": {"name": "backup-agent-8f2c6d4a1-q9m7k", "namespace": "production",
                         "labels": {"app": "backup-agent", "tier": "ops", "privileged": "true"}},
            "spec": {"serviceAccountName": "backup-agent-sa",
                     "containers": [{"name": "backup", "image": "novacorp/backup-agent:1.2.0",
                                     "env": [{"name": "BACKUP_SCHEDULE", "value": "0 2 * * *"}],
                                     "volumeMounts": [{"name": "sa-token", "mountPath": "/var/run/secrets/kubernetes.io/serviceaccount"}]}]},
            "status": {"phase": "Running", "podIP": "10.244.0.22"},
        },
    ]
}

CONFIGMAPS_DATA = {
    "kind": "ConfigMapList",
    "apiVersion": "v1",
    "items": [
        {"metadata": {"name": "payments-config", "namespace": "production"},
         "data": {"DB_HOST": "postgres-primary.production.svc", "DB_PORT": "5432",
                  "PAYMENT_GATEWAY": "https://api.stripe.internal"}},
        {"metadata": {"name": "redis-config", "namespace": "production"},
         "data": {"REDIS_HOST": "redis-master-0.production.svc", "REDIS_PORT": "6379",
                  "MAX_MEMORY": "512mb"}},
        {"metadata": {"name": "nginx-config", "namespace": "production"},
         "data": {"worker_processes": "4", "TODO": "Move admin password into Secret later. Current: N0v4C0rp_4dm1n_2024"}},
        {"metadata": {"name": "monitoring-config", "namespace": "production"},
         "data": {"PROMETHEUS_ENDPOINT": "http://prometheus.monitoring.svc:9090",
                  "ALERT_CHANNEL": "#prod-alerts"}},
    ]
}


def get_secrets_data():
    flag_b64 = base64.b64encode(FLAG.encode()).decode()
    return {
        "kind": "SecretList",
        "apiVersion": "v1",
        "items": [
            {"metadata": {"name": "db-password", "namespace": "production", "type": "Opaque"},
             "data": {"password": base64.b64encode(b"postgres_r00t_n0vac0rp!").decode()}},
            {"metadata": {"name": "aws-credentials", "namespace": "production", "type": "Opaque"},
             "data": {"access_key": base64.b64encode(b"AKIAIOSFODNN7EXAMPLE").decode(),
                      "secret_key": base64.b64encode(b"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY").decode()}},
            {"metadata": {"name": "jwt-signing-key", "namespace": "production", "type": "Opaque"},
             "data": {"key": base64.b64encode(b"n0v4c0rp_jwt_sup3r_s3cr3t_k3y").decode()}},
            {"metadata": {"name": "monitoring-token", "namespace": "production", "type": "Opaque"},
             "data": {"token": base64.b64encode(b"prom_readonly_token_xk29f").decode()}},
            {"metadata": {"name": "flag-secret", "namespace": "production", "type": "Opaque"},
             "data": {"flag": flag_b64}},
        ]
    }


def get_secret_by_name(name):
    secrets = get_secrets_data()
    for s in secrets["items"]:
        if s["metadata"]["name"] == name:
            return s
    return None


BACKUP_POD_LOGS = """[2026-07-06T02:00:01Z] backup-agent starting scheduled run
[2026-07-06T02:00:02Z] authenticating with service account: backup-agent-sa
[2026-07-06T02:00:02Z] token loaded from /var/run/secrets/kubernetes.io/serviceaccount/token
[2026-07-06T02:00:03Z] connected to kubernetes API at kubernetes.default.svc
[2026-07-06T02:00:04Z] enumerating secrets in namespace: production
[2026-07-06T02:00:05Z] backing up 5 secrets to encrypted storage
[2026-07-06T02:00:08Z] backup completed successfully
[2026-07-06T02:00:08Z] next run at 2026-07-07T02:00:00Z
"""


class K8sAPIHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        auth = self.headers.get("Authorization", "")
        token = auth.replace("Bearer ", "") if auth.startswith("Bearer ") else ""

        if self.path == "/api":
            self._json(200, {"kind": "APIVersions", "versions": ["v1"]})
            return

        if self.path == "/api/v1":
            self._json(200, {
                "kind": "APIResourceList",
                "groupVersion": "v1",
                "resources": [
                    {"name": "pods", "namespaced": True, "kind": "Pod", "verbs": ["get", "list"]},
                    {"name": "pods/log", "namespaced": True, "kind": "Pod", "verbs": ["get"]},
                    {"name": "pods/exec", "namespaced": True, "kind": "Pod", "verbs": ["create"]},
                    {"name": "services", "namespaced": True, "kind": "Service", "verbs": ["get", "list"]},
                    {"name": "secrets", "namespaced": True, "kind": "Secret", "verbs": ["get", "list"]},
                    {"name": "configmaps", "namespaced": True, "kind": "ConfigMap", "verbs": ["get", "list"]},
                ]
            })
            return

        if not token:
            self._json(401, {"kind": "Status", "status": "Failure",
                             "message": "Unauthorized", "reason": "Unauthorized", "code": 401})
            return

        # Frontend SA: can list pods, configmaps, pod logs. CANNOT list secrets.
        if token == SERVICE_ACCOUNT_TOKEN:
            if self.path == "/api/v1/namespaces/production/pods":
                self._json(200, PODS_DATA)
            elif self.path == "/api/v1/namespaces/production/configmaps":
                self._json(200, CONFIGMAPS_DATA)
            elif self.path.startswith("/api/v1/namespaces/production/pods/") and "/log" in self.path:
                pod_name = self.path.split("/pods/")[1].split("/log")[0]
                if "backup-agent" in pod_name:
                    self._text(200, BACKUP_POD_LOGS)
                else:
                    self._text(200, f"[INFO] Pod {pod_name} running normally\n[INFO] No recent events\n")
            elif "/exec" in self.path and "backup-agent" in self.path:
                self._text(200, BACKUP_TOKEN)
            elif self.path == "/api/v1/namespaces/production/secrets":
                self._json(403, {"kind": "Status", "status": "Failure",
                                 "message": "secrets is forbidden: User \"system:serviceaccount:production:frontend-sa\" cannot list resource \"secrets\" in namespace \"production\"",
                                 "reason": "Forbidden", "code": 403})
            elif self.path.startswith("/api/v1/namespaces/production/secrets/"):
                self._json(403, {"kind": "Status", "status": "Failure",
                                 "message": "secrets is forbidden: User \"system:serviceaccount:production:frontend-sa\" cannot get resource \"secrets\" in namespace \"production\"",
                                 "reason": "Forbidden", "code": 403})
            else:
                self._json(404, {"kind": "Status", "status": "Failure", "message": "not found", "code": 404})
            return

        # Backup SA: can list and get secrets (the pivot target)
        if token == BACKUP_TOKEN:
            if self.path == "/api/v1/namespaces/production/secrets":
                self._json(200, get_secrets_data())
            elif self.path.startswith("/api/v1/namespaces/production/secrets/"):
                secret_name = self.path.split("/secrets/")[1]
                secret = get_secret_by_name(secret_name)
                if secret:
                    self._json(200, secret)
                else:
                    self._json(404, {"kind": "Status", "status": "Failure", "message": "not found", "code": 404})
            elif self.path == "/api/v1/namespaces/production/pods":
                self._json(200, PODS_DATA)
            else:
                self._json(403, {"kind": "Status", "status": "Failure", "message": "forbidden", "code": 403})
            return

        self._json(401, {"kind": "Status", "status": "Failure", "message": "Unauthorized", "code": 401})

    def _json(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _text(self, code, text):
        body = text.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve(port=6443):
    init_tokens()
    server = HTTPServer(("127.0.0.1", port), K8sAPIHandler)
    print(f"[k8s-api] Simulated API server on 127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    serve()
