# 0auth::c0nfus10n

**Category:** Web  
**Difficulty:** Hard+  
**Points:** 600  
**Author:** H3xPh4r04h  
**Flag Format:** `warCTF{...}`  
**Ports:** 8080 (Client App), 9000 (Auth Server)  

---

> *"We built our own OAuth server. In-house. From scratch. It's bulletproof."*
> - CTO, 2 weeks before the breach

SecureAuth Inc. launched their shiny new OAuth 2.0 system. Authorization server, client app, JWT tokens, JWKS endpoint - the works.

They disabled the documentation. They obfuscated the client IDs. They added state parameters. They think they're safe.

But the token endpoint doesn't check who the code was issued to. And the redirect validation is... generous.

**Prove them wrong.**

## Hints

1. OAuth has many moving parts. What happens if the redirect URI validation is... flexible?
2. The authorization server and the client application trust each other. Maybe too much.
3. Tokens tell stories. Read them carefully.
4. Who validates what? The client trusts the auth server, but does the auth server validate the client?
5. Sometimes the state parameter isn't enough protection.
6. Look at how the `aud` (audience) claim is handled during token exchange.

## Connection

```
http://<host>:8080   (Client App)
http://<host>:9000   (Auth Server)
```
