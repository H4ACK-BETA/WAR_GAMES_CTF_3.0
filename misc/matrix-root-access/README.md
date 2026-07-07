# matrix://root_access

Reverse Engineering + Binary Exploitation (Medium-Hard)
Expected solve time: 60-120 minutes for intermediate players.

> "Unfortunately, no one can be told what the Matrix is. You have to see
> it for yourself." - Morpheus

## Files

| File               | Purpose                                                             |
|--------------------|----------------------------------------------------------------------|
| `chall.c`          | Challenge source. Contains the placeholder secret patched per build. |
| `gen_challenge.py` | Picks a random phrase + XOR key, patches `chall.c` at build time.    |
| `Dockerfile`       | Two-stage build: compiles the patched binary, slim non-root runtime. |
| `start.sh`         | GZCTF flag handling (`GZCTF_FLAG` -> `/flag.txt`, env scrubbed) + hands off to xinetd. |
| `ctf.xinetd`       | xinetd service definition: forks the binary per connection as the unprivileged `ctf` user. |
| `docker-compose.yml` | Local testing harness.                                              |
| `solve.py`         | Reference pwntools exploit, used to validate every build.            |

## Player-facing flow

1. Connect to the service. A public menu offers three harmless options
   (Connect, About, Exit) -- nothing hints at hidden functionality.
2. Reverse engineer the binary (Ghidra/IDA). The menu's `switch` reveals
   an undocumented branch reachable with input `1337`, which calls
   `attempt_hidden_login()`.
3. `attempt_hidden_login()` calls `validate_phrase()`, which XORs the
   player's input against an embedded byte array. Recovering the XOR
   key (a single byte, visible as an immediate in the disassembly) and
   the array lets the player compute the plaintext access phrase.
4. Supplying the correct phrase drops the player into the
   `morpheus_console()` menu.
5. The console's "Send Transmission" option calls `transmit()`, which
   reads into a 64-byte stack buffer via `gets()` with no bounds check,
   no stack canary, and no PIE.
6. The player locates `become_the_one()` (recognizable by its
   `fopen("/flag.txt")` + read loop even after stripping) and builds a
   classic ret2win payload: 64 bytes padding + 8 bytes for saved RBP +
   the address of `become_the_one()`.
7. Function return hijacks control flow into `become_the_one()`, which
   prints the flag.

## Build-time randomization

Every container build runs `gen_challenge.py`, which:
- Picks one phrase at random from an 8-entry wordlist (14-25 chars).
- Picks a random XOR key (1-255).
- Patches both into `chall.c` before compilation.

`become_the_one()`'s address (`0x4016b8`) is **stable across all
builds** regardless of which phrase/key combination is chosen, since
the encrypted secret lives in `.data`, not `.text`, and the binary is
compiled `-no-pie`. This was explicitly verified against the shortest
and longest wordlist entries -- the solving methodology never changes
between teams, only the phrase and the flag do.

For deterministic/reproducible local builds, pass a seed:
```
python3 gen_challenge.py my-fixed-seed
```
Omit the seed (as the production Dockerfile does by default) for a
truly random per-team build.

## Compiler flags (intentional weaknesses)

```
gcc -fno-stack-protector -no-pie -z execstack -O0 -o chall chall.c
```

- `-fno-stack-protector` -- no canary, so the overflow isn't caught.
- `-no-pie` -- fixed addresses; `become_the_one()` is always at
  `0x4016b8`, no leak required.
- `-z execstack` -- not exploited by the intended solution, but left
  enabled in case players explore shellcode-based alternate paths.
- `-O0` -- keeps the disassembly close to the source for readability
  during reverse engineering.

## GZCTF flag handling

Same pattern as other challenges in this set:
1. `start.sh` reads `GZCTF_FLAG` and writes it to `/flag.txt` (mode 400,
   owned by the unprivileged `ctf` user). The flag is never embedded in
   the binary or the image.
2. `GZCTF_FLAG` is `unset` from the shell's environment.
3. `exec /usr/sbin/xinetd -dontfork` replaces the shell's process
   image, so the resulting `xinetd` process (and every connection it
   forks afterward) never has `GZCTF_FLAG` in `/proc/<pid>/environ`.
4. `xinetd` listens on port 9999 (see `/etc/xinetd.d/ctf`) and forks a
   fresh copy of the challenge binary per incoming connection, running
   it as the unprivileged `ctf` user (the `user = ctf` directive); only
   that user can read `/flag.txt`.
5. `per_source`, `rlimit_cpu`, and `instances` limits in `ctf.xinetd`
   cap how many simultaneous connections one source IP or the service
   as a whole can hold open, and how much CPU time a single connection
   may consume.

## Validation performed

- Compiled and ran with a fixed seed and with fully random seeds;
  confirmed `become_the_one()` stays at a stable address across the
  full range of wordlist entry lengths.
- Confirmed stripped binaries behave identically to unstripped ones and
  that the win-function address survives stripping (only the symbol
  *name* is removed).
- Ran the full reference exploit (`solve.py`) against both stripped and
  unstripped local binaries and recovered the flag successfully.
- Simulated the `GZCTF_FLAG` -> `/flag.txt` -> `unset` -> `exec` flow
  directly (no Docker available in the authoring sandbox) and confirmed
  via `/proc/self/environ` inspection that the flag does not leak into
  the final process's environment.
- Verified the binary degrades gracefully (clean exit / isolated
  segfault, no broader crash) on garbage menu input and on
  under/over-length overflow payloads that don't hit the exact offset.

## Known limitation in authoring environment

This package was built and validated without direct Docker access (no
Docker daemon in the authoring sandbox). The Dockerfile and
`docker-compose.yml` use the standard, well-documented two-stage build
pattern already proven on this set's other challenges, and every other
component (compile flags, address stability, exploit, flag-handling
shell logic) was tested directly. **Before competition deployment, run
`docker compose up --build` once and confirm `solve.py HOST 9999`
recovers the flag end-to-end against the actual container.**

### Fixed: missing libc6-dev in builder stage

First real Docker build caught a bug the sandbox couldn't: the builder
stage installed `gcc` but not `libc6-dev`, so `stdio.h` and the rest of
the standard headers weren't present and the compile failed with
`fatal error: stdio.h: No such file or directory`. `gcc` alone is just
the compiler driver; the C headers and static libs come from
`libc6-dev` on Debian. Fixed by adding `libc6-dev` alongside `gcc` and
`python3` in the builder stage's `apt-get install`.

### Switched: socat -> xinetd

The runtime front-end was switched from `socat` to `xinetd`, matching
the more traditional CTF pwn deployment pattern. Key differences from
the socat version:

- `ctf.xinetd` (installed to `/etc/xinetd.d/ctf`) replaces the
  `EXEC:...,su=ctf` socat address -- it declares the service, port,
  user to run as, and per-connection safety limits (`per_source`,
  `rlimit_cpu`, `instances`) declaratively instead of as command-line
  flags.
- `start.sh` no longer execs the front-end with the binary path baked
  into the command line; it execs `/usr/sbin/xinetd -dontfork`, which
  reads the package's default `/etc/xinetd.conf` (which includes
  `/etc/xinetd.d/`) and starts the `ctf` service defined there. The
  `unset GZCTF_FLAG` -> `exec` ordering and guarantee are unchanged --
  verified directly via `/proc/self/environ` inspection again after
  the swap.
- The Dockerfile installs `xinetd` instead of `socat`, copies
  `ctf.xinetd` into `/etc/xinetd.d/ctf`, and creates `/etc/banner_fail`
  (shown to a client on access-control rejection).
