# Commands

## Build

```bash
docker build -t your-registry.com/matrix-root:latest .
```

## Extract player binary (stripped, for handout)

```bash
docker build --target dist --output type=local,dest=./chall-dist .
```

## Push to registry

```bash
docker push your-registry.com/matrix-root:latest
```

## GZCTF Configuration

- Image: `your-registry.com/matrix-root:latest`
- Port: `9888`
- Flag variable is auto-injected as `GZCTF_FLAG`

## Local test

```bash
docker run -d -p 9888:9888 -e GZCTF_FLAG="flag{test_flag}" your-registry.com/matrix-root:latest
```

## Run solve script

```bash
python3 solve.py                      # local binary
python3 solve.py <host> <port>        # remote
```

## Find gadgets in binary

```bash
ROPgadget --binary ./chall-dist/challenge | grep "pop rdi"
strings -t x ./chall-dist/challenge | grep "/bin/cat"
objdump -d ./chall-dist/challenge | grep "system@plt"
```
