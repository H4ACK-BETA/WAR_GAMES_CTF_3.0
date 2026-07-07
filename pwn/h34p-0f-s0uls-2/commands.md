# H34p 0f S0uls II - Docker Commands

## Build

```bash
docker build -t h34p-0f-s0uls-2 h34p-0f-s0uls-2/
```

## Run

```bash
docker run -d -p 9999:9999 -e FLAG="WarCTF{l1ch_k1ng_d3f34t3d}" --name h34p2 h34p-0f-s0uls-2
```

## Extract Binary + Libc for Player Attachments

```bash
id=$(docker create h34p-0f-s0uls-2)
docker cp $id:/challenge/challenge h34p-0f-s0uls-2/chall-dist/challenge
docker cp $id:/lib/x86_64-linux-gnu/libc.so.6 h34p-0f-s0uls-2/chall-dist/libc.so.6
docker cp $id:/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2 h34p-0f-s0uls-2/chall-dist/ld-linux-x86-64.so.2
docker rm $id
```

## Stop & Cleanup

```bash
docker stop h34p2
docker rm h34p2
```

## Test Locally

```bash
echo "test" | nc localhost 9999
```

## GzCTF Deployment

Set environment variable in platform:
```
GZCTF_FLAG=WarCTF{your_flag_here}
```
