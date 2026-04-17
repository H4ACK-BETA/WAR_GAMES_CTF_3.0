# WARGAMES_CTF_3.0

## GZCTF Repo

### This repository contains challenges designed for the **GZCTF** platform, utilizing dynamic container orchestration and static attachment hosting.

### Repository Structure

```
.
├── challenges/
│   ├── web/
│   │   └── chall-name/
│   │       ├── Dockerfile      # The recipe GZCTF will use
│   │       ├── build.sh        # Script to build the local image
│   │       ├── challenge.json  # GZCTF settings
│   │       └── src/            # App source code
│   ├── pwn/
│   │   └── chall-name/
│   │       ├── Dockerfile
│   │       ├── build.sh
│   │       └── src/            # Binary source
│   └── [static-cats]/          # Crypto, Forensics, etc.
│       └── attachments/        # Files to upload to GZCTF
└── build_all.sh                # Master script to build everything locally
```


### Include Challenge Author's Name in respective challenge description.
