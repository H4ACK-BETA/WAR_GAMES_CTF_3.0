# CTF Challenges Repository

## 📁 Directory Structure

```
.
├── pwn/        # Binary exploitation challenges
├── reverse/    # Reverse engineering challenges
└── web/        # Web security challenges
```

## 🧩 Challenge Directory Layout

Each challenge follows a consistent structure for portability and deployment.

```
challenge-name/
├── chall-dist/           # Distributed files for players (binaries, etc.)
├── src/                  # Source code of the challenge
├── Dockerfile            # Container setup
├── start.sh              # Entry point script
├── run.sh                # Runtime execution script
├── solve.py              # Reference exploit/solution
├── gzctf-challenge.json  # GZCTF metadata/config
├── xinetd.conf           # Service config (if applicable)
└── xinetd.d/             # Service definitions
```

---

## 🧪 Solver Scripts

Every challenge includes a `solve.py` used for:
- Internal validation
- Demonstrating the intended exploit path

---

## 📌 NOTE

- Keep `chall-dist/` minimal — only player-facing files
- Do **not** expose source unless intended
- Use Docker for isolation
- Validate with `solve.py` before deployment
- Keep configs consistent across categories

---
