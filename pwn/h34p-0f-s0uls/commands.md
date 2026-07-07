# H34p 0f S0uls — Docker Commands

## Build

```bash
docker build -t h34p-0f-s0uls h34p-0f-s0uls/
```

## Run

```bash
docker run -d -p 9999:9999 -e FLAG="WarCTF{h34p_0v3rfl0w_m4st3r}" --name h34p h34p-0f-s0uls
```

## Extract Binary + Libc for Player Attachments

```bash
id=$(docker create h34p-0f-s0uls)
docker cp $id:/challenge/challenge h34p-0f-s0uls/chall-dist/challenge
docker cp $id:/lib/x86_64-linux-gnu/libc.so.6 h34p-0f-s0uls/chall-dist/libc.so.6
docker cp $id:/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2 h34p-0f-s0uls/chall-dist/ld-linux-x86-64.so.2
docker rm $id
```

## Stop & Cleanup

```bash
docker stop h34p
docker rm h34p
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
