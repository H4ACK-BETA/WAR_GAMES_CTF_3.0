# OAuth Confusion

**Category:** Web  
**Difficulty:** Hard+  
**Points:** 600  
**Author:** H3xPh4r04h  

## Description

SecureAuth Inc. just launched their shiny new OAuth 2.0 login system. They even built their own authorization server to keep things "in-house."

They claim it's bulletproof. Prove them wrong.

## Hints

1. OAuth has many moving parts. What happens if the redirect URI validation is... flexible?
2. The authorization server and the client application trust each other. Maybe too much.
3. Tokens tell stories. Read them carefully.
4. Who validates what? The client trusts the auth server, but does the auth server validate the client?
5. Sometimes the state parameter isn't enough protection.
6. Look at how the `aud` (audience) claim is handled during token exchange.

## Connection

```
http://<host>:<port>
```
