# Image CDN - Web Challenge (Medium-Hard)

ImageMagick SSRF via SVG processing → internal metadata service → admin credentials → flag.

## Quick Start (Local Testing)

```bash
docker-compose up --build
# Access at http://localhost:8081
```

## GZCTF Deployment

- **Type:** Dynamic container
- **Port:** 8080 (HTTP)
- **Flag:** Set via `GZCTF_FLAG` or `FLAG` env var
- **Image:** Build from Dockerfile

## Attack Flow

1. Discover the CDN accepts SVG uploads
2. Craft SVG with `<image xlink:href="http://127.0.0.1:8888/credentials">`
3. Upload - ImageMagick processes SVG and fetches the internal metadata service
4. The rendered PNG output contains the JSON credentials as embedded content
5. Extract admin credentials: `cdn_admin` / `S3cur3_CDN_Adm1n_2024!`
6. Login at `/admin` with extracted credentials
7. Admin dashboard displays the flag

## Key Vulnerability

ImageMagick's SVG processor follows external URL references (`xlink:href`).
The `policy.xml` is intentionally permissive (allows all coders and delegates).
The internal metadata service on `127.0.0.1:8888` is not exposed externally
but is reachable from the server via SSRF.

## Solve

```bash
python solve.py <host> <port>
```
