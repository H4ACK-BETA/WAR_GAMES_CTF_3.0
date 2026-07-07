# matrix://root_access -- "Jaswanth's Machine" (Hardened)

Reverse Engineering + Binary Exploitation (Medium-Hard) - 550 pts

## Challenge Summary

A multi-stage pwn challenge requiring:
1. Reverse engineering a rolling multi-byte XOR encryption
2. Discovering a hidden menu code
3. Leaking a per-session stack sentinel via format string vulnerability
4. Building a ROP chain to call `system("/bin/cat /flag")`

## What makes this harder than the original

| Aspect | Original | Hardened |
|--------|----------|---------|
| XOR encryption | Single-byte static XOR | Rolling multi-byte XOR with key evolution |
| Hidden code | `1337` | `31337` |
| Win function | Direct `become_the_one()` ret2win | No win function; must ROP to `system()` |
| Stack protection | None | Custom sentinel value (must be preserved in overflow) |
| Sentinel value | N/A | Randomized per-session (`0xDEAD????`) |
| Leak mechanism | N/A | Format string vulnerability in "Signal Echo Test" |
| Exploit complexity | Overwrite RIP with one address | Leak sentinel + preserve it + ROP chain |

## Solve Steps

1. **Load binary in Ghidra.** Find the public menu's hidden `default`
   branch that checks for `31337`.

2. **Reverse the encryption.** In `validate_phrase()`, identify the
   rolling XOR scheme:
   - Base key from `#define XOR_KEY`
   - For each byte: XOR with `(key + r*0x11)` for `r = 0..2` (3 rounds)
   - Key evolves: `key = (key ^ i) + 0x07`
   - Extract `encrypted_secret[]` and reverse the operation.

3. **Find the format string vulnerability.** Menu option 3 ("Signal
   Echo Test") passes user input directly to `printf()`. Use `%p` spray
   to dump stack values.

4. **Leak the sentinel.** The per-session sentinel has the form
   `0xDEAD????` (top 16 bits = `0xDEAD`, bottom 16 randomized from
   `time(NULL) ^ getpid()`). Identify it among leaked stack values.

5. **Enter the hidden console.** Send `31337`, then the decrypted phrase.

6. **Identify ROP targets** in the stripped binary:
   - `system@plt` (linked because of `gadget_anchor()`)
   - The string `"/bin/cat /flag"` in `.rodata`
   - A `pop rdi; ret` gadget (commonly at end of `__libc_csu_init`)

7. **Build the overflow payload:**
   ```
   [64 bytes filler] [4-byte sentinel] [4 bytes padding] [8-byte fake RBP]
   [ret gadget] [pop rdi; ret] [addr of "/bin/cat /flag"] [system@plt]
   ```
   The sentinel must be placed at the correct stack offset to pass the
   corruption check before the function returns.

8. **Send it.** The ROP chain fires, `system("/bin/cat /flag")` executes,
   flag prints.

## Files

| File | Purpose |
|---|---|
| `src/challenge.c` | Challenge source with rolling XOR, format string vuln, sentinel check, ROP target |
| `src/gen_challenge.py` | Per-build randomizer: random phrase + key, multi-round encryption |
| `Dockerfile` | Two-stage build: patched source → compiled binary, slim runtime |
| `start.sh` | Flag injection (`GZCTF_FLAG` / `FLAG` / fallback → `/flag`) + xinetd |
| `run.sh` | Per-connection exec wrapper |
| `xinetd.conf` / `xinetd.d/matrix-root-access` | Service config, port 9888 |
| `chall-dist/challenge` | **Built from Dockerfile** - stripped binary for player download (use `--target dist`) |
| `solve.py` | Reference pwntools exploit (requires adjusting phrase per-build) |
| `description.md` | Player-facing challenge description |

## Build & Deploy

```bash
# Build the service image (randomized per seed)
docker build --build-arg BUILD_SEED="team-$(date +%s)" -t matrix-root .

# Extract the stripped binary for player distribution
docker build --target dist --output type=local,dest=./chall-dist .

# Run with flag
docker run -d -p 9888:9888 -e GZCTF_FLAG="flag{your_flag_here}" matrix-root
```

The `--target dist` build exports just the stripped binary to `chall-dist/challenge`.
This is what gets handed to players alongside the remote host:port.
The service container (`runtime` stage) runs the **unstripped** binary internally.

## Compilation Flags

```
gcc -fno-stack-protector -no-pie -z execstack -O0
```

- `-fno-stack-protector`: No compiler canaries (we use our own sentinel)
- `-no-pie`: Fixed addresses for ROP gadgets
- `-z execstack`: Executable stack (not strictly needed for this ROP, but removes NX as a red herring)
- `-O0`: Predictable stack layout

## Difficulty Calibration

- **RE component** (rolling XOR): Intermediate - requires understanding the key evolution, not just a single XOR
- **Leak component** (format string): Beginner-Intermediate - standard `%p` spray, but identifying the sentinel among many values adds a filtering step
- **Exploitation** (ROP + sentinel): Intermediate - players must juggle preserving the sentinel AND building a valid chain
- **Overall**: Medium-Hard, ~550 pts is appropriate for teams with some pwn experience

## Hints (if you want to release progressively)

1. "The menu has more than meets the eye. Way more."
2. "Jaswanth's encryption isn't just XOR. It evolves."
3. "That echo test is surprisingly... revealing."
4. "The sentinel guards the gate. But gates can be walked through if you know the password."
5. "No backdoor function this time. But the tools you need are already linked in."

## Known Limitation

The exact stack offset of the sentinel relative to the buffer depends on
compiler version and optimization level. The solve script may need its
padding adjusted if rebuilt with a different GCC version. Test the actual
binary's layout with GDB before competition.
