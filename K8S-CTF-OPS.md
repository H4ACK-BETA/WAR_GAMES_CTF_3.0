# K8s CTF Operations - Debug & Management Commands

Quick reference for running, debugging, and managing CTF challenges on Kubernetes during competition.

---

## Cluster Health

```bash
# Cluster info
kubectl cluster-info
kubectl get nodes -o wide
kubectl top nodes

# All resources in CTF namespace
kubectl get all -n ctf
kubectl get all -A

# Events (recent issues surface here first)
kubectl get events -n ctf --sort-by='.lastTimestamp' | tail -30
kubectl get events -A --field-selector type=Warning
```

---

## Pod Management

```bash
# List all challenge pods
kubectl get pods -n ctf -o wide
kubectl get pods -A -o wide

# Watch pods in real-time
kubectl get pods -n ctf -w

# Pod details (scheduling issues, image pull errors, etc.)
kubectl describe pod <pod-name> -n ctf

# Pod status summary
kubectl get pods -n ctf --field-selector status.phase!=Running

# Restart a stuck pod
kubectl delete pod <pod-name> -n ctf
kubectl rollout restart deployment <deployment-name> -n ctf

# Force kill a pod
kubectl delete pod <pod-name> -n ctf --grace-period=0 --force

# Scale a challenge up/down
kubectl scale deployment <name> -n ctf --replicas=0
kubectl scale deployment <name> -n ctf --replicas=1
```

---

## Logs & Debugging

```bash
# Pod logs
kubectl logs <pod-name> -n ctf
kubectl logs <pod-name> -n ctf --tail=50
kubectl logs <pod-name> -n ctf -f            # follow
kubectl logs <pod-name> -n ctf --previous    # crashed container's last logs

# Multi-container pod
kubectl logs <pod-name> -n ctf -c <container-name>

# All pods matching a label
kubectl logs -l app=baby-pwn -n ctf --tail=20

# Exec into a running pod
kubectl exec -it <pod-name> -n ctf -- /bin/bash
kubectl exec -it <pod-name> -n ctf -- /bin/sh

# Run a one-off debug command
kubectl exec <pod-name> -n ctf -- cat /flag
kubectl exec <pod-name> -n ctf -- ps aux
kubectl exec <pod-name> -n ctf -- netstat -tlnp
kubectl exec <pod-name> -n ctf -- curl -s localhost:8080/health
```

---

## Deployments & Services

```bash
# List deployments
kubectl get deployments -n ctf
kubectl get svc -n ctf

# Check rollout status
kubectl rollout status deployment <name> -n ctf

# View deployment config
kubectl get deployment <name> -n ctf -o yaml

# Update image (re-deploy)
kubectl set image deployment/<name> <container>=<new-image> -n ctf

# Rollback
kubectl rollout undo deployment <name> -n ctf

# Check endpoints (service → pod mapping)
kubectl get endpoints -n ctf
```

---

## Networking & Connectivity

```bash
# Check service/ingress
kubectl get svc -n ctf -o wide
kubectl get ingress -n ctf

# Port forward for local testing
kubectl port-forward svc/<service-name> 8080:8080 -n ctf
kubectl port-forward pod/<pod-name> 9999:9999 -n ctf

# DNS resolution test (from inside a pod)
kubectl exec <pod-name> -n ctf -- nslookup kubernetes.default.svc
kubectl exec <pod-name> -n ctf -- wget -qO- http://service-name:port/health

# Test connectivity from a debug pod
kubectl run debug --rm -it --image=busybox -n ctf -- /bin/sh
# inside: wget -qO- http://challenge-svc:8080/
```

---

## Resource Usage

```bash
# Pod resource consumption
kubectl top pods -n ctf
kubectl top pods -n ctf --sort-by=memory

# Node resources
kubectl top nodes

# Check resource requests/limits
kubectl get pods -n ctf -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].resources}{"\n"}{end}'

# Find OOMKilled pods
kubectl get pods -n ctf -o json | jq '.items[] | select(.status.containerStatuses[0].lastState.terminated.reason=="OOMKilled") | .metadata.name'
```

---

## Secrets & ConfigMaps

```bash
# List secrets
kubectl get secrets -n ctf
kubectl get configmaps -n ctf

# View a secret (base64 decoded)
kubectl get secret <name> -n ctf -o jsonpath='{.data.flag}' | base64 -d

# Create/update a flag secret
kubectl create secret generic flag-secret -n ctf --from-literal=flag='WarCTF{...}' --dry-run=client -o yaml | kubectl apply -f -

# Verify flag is set correctly
kubectl exec <pod-name> -n ctf -- cat /flag
```

---

## GZCTF Specific

```bash
# Check GZCTF platform pods
kubectl get pods -n gzctf
kubectl logs -l app=gzctf -n gzctf --tail=50

# GZCTF database
kubectl get pods -n gzctf -l app=postgres

# Check dynamic container provisioning
kubectl get pods -n ctf --watch

# See challenge container env vars
kubectl get pod <pod-name> -n ctf -o jsonpath='{.spec.containers[0].env}'

# Check if flag env is injected
kubectl exec <pod-name> -n ctf -- printenv | grep FLAG
```

---

## Image & Registry Issues

```bash
# Check image pull status
kubectl get events -n ctf --field-selector reason=Failed
kubectl get events -n ctf --field-selector reason=Pulling

# Describe pod for ImagePullBackOff details
kubectl describe pod <pod-name> -n ctf | grep -A5 "Events"

# Verify image exists (if using local registry)
docker images | grep <challenge-name>
crictl images | grep <challenge-name>

# Manually pull an image on a node
docker pull <registry>/<image>:<tag>
```

---

## Common Issues & Fixes

### Pod stuck in Pending
```bash
kubectl describe pod <pod-name> -n ctf
# Usually: insufficient resources, node selector mismatch, PVC not bound
kubectl get nodes -o custom-columns=NAME:.metadata.name,CPU:.status.allocatable.cpu,MEM:.status.allocatable.memory
```

### Pod in CrashLoopBackOff
```bash
kubectl logs <pod-name> -n ctf --previous
kubectl describe pod <pod-name> -n ctf | grep -A10 "State:"
# Fix: check start.sh, missing deps, bad flag env
```

### Connection refused / timeout
```bash
# Check pod is running and ready
kubectl get pod <pod-name> -n ctf -o jsonpath='{.status.conditions}'

# Check service selector matches pod labels
kubectl get svc <svc-name> -n ctf -o yaml | grep selector -A5
kubectl get pods -n ctf --show-labels

# Check if port is actually listening inside pod
kubectl exec <pod-name> -n ctf -- ss -tlnp
```

### Flag not showing / empty
```bash
# Check flag injection
kubectl exec <pod-name> -n ctf -- cat /flag
kubectl exec <pod-name> -n ctf -- printenv | grep -i flag

# Check start.sh ran correctly
kubectl logs <pod-name> -n ctf | head -5
```

### High load / players DDoSing
```bash
# Check which pods are consuming resources
kubectl top pods -n ctf --sort-by=cpu

# Rate limit via network policy or HPA
kubectl get hpa -n ctf

# Kill all pods for a challenge and let deployment recreate
kubectl delete pods -l app=<challenge> -n ctf
```

---

## Bulk Operations

```bash
# Restart ALL challenge pods
kubectl delete pods --all -n ctf

# Scale all deployments to 0 (emergency shutdown)
kubectl get deployments -n ctf -o name | xargs -I{} kubectl scale {} --replicas=0 -n ctf

# Scale all back up
kubectl get deployments -n ctf -o name | xargs -I{} kubectl scale {} --replicas=1 -n ctf

# Get all pod IPs
kubectl get pods -n ctf -o custom-columns=NAME:.metadata.name,IP:.status.podIP

# Export all challenge configs
kubectl get deployments,svc,ingress -n ctf -o yaml > ctf-backup.yaml
```

---

## Pre-Competition Checklist

```bash
# 1. Verify all challenges are running
kubectl get pods -n ctf | grep -v Running

# 2. Test each challenge endpoint
for svc in $(kubectl get svc -n ctf -o jsonpath='{.items[*].metadata.name}'); do
  echo -n "$svc: "
  kubectl exec deploy/debug-pod -n ctf -- curl -s -o /dev/null -w "%{http_code}" http://$svc:8080/ 2>/dev/null
  echo
done

# 3. Verify flags are set
for pod in $(kubectl get pods -n ctf -o jsonpath='{.items[*].metadata.name}'); do
  echo -n "$pod: "
  kubectl exec $pod -n ctf -- cat /flag 2>/dev/null | head -1
  echo
done

# 4. Check resource headroom
kubectl top nodes
kubectl describe nodes | grep -A5 "Allocated resources"

# 5. Verify DNS resolution
kubectl run dns-test --rm -it --image=busybox -n ctf --restart=Never -- nslookup kubernetes.default.svc

# 6. Check storage
kubectl get pvc -n ctf
df -h  # on nodes
```

---

## During Competition Monitoring

```bash
# Live dashboard (run in tmux pane)
watch -n5 'kubectl get pods -n ctf -o wide'

# Stream all events
kubectl get events -n ctf -w

# Quick health check loop
while true; do
  echo "=== $(date) ==="
  kubectl get pods -n ctf --no-headers | awk '{print $1, $3}' | grep -v Running
  sleep 30
done
```

---

## Cleanup (Post-Competition)

```bash
# Delete all challenge resources
kubectl delete namespace ctf

# Or selective cleanup
kubectl delete deployments --all -n ctf
kubectl delete svc --all -n ctf
kubectl delete secrets --all -n ctf
kubectl delete configmaps --all -n ctf

# Remove images from nodes
docker system prune -af
crictl rmi --prune
```
