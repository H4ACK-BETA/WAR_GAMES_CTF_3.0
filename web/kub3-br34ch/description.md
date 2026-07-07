# kub3::br34ch

**Category:** Web + Cloud  
**Difficulty:** Hard  
**Author:** H3xPh4r04h  

---

> *"We turned off the dashboard. Nobody can get in. The cluster is invisible."*
> — Lead DevOps, 3 days before the breach

## Story

NovaCorp's golden startup just closed Series B. First order of business: migrate everything to Kubernetes. "Enterprise-grade. Battle-tested. Unhackable," the pitch deck said.

The DevOps team disabled the Kubernetes Dashboard, locked the firewall, and called it a day. But inside the cluster, every pod still carries an identity. A name. A token. A key to the kingdom.

You got access to their internal status page — some Flask app a junior dev shipped without review. It has a URL fetcher. "For monitoring," they said.

The cluster is listening. The tokens are mounted. The secrets are waiting.

**Get in. Escalate. Exfiltrate.**

## Hints

1. Pods have identities. They don't need to ask for them.
2. Credentials live where the kubelet puts them. Always the same path.
3. `kubernetes.default.svc` — every pod knows this address.
4. Base64 is encoding. Not encryption.
5. Not every pod has the same permissions.

## Connection

```
http://<host>:<port>
```
