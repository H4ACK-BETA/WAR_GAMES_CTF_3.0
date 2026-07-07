# 4p1::pl4ygr0und

**Category:** Web  
**Difficulty:** Hard  
**Points:** 500  
**Author:** H3xPh4r04h  
**Flag Format:** `warCTF{...}`  
**Ports:** 8080 (HTTP), 50051 (gRPC)  

---

> *"We support REST, GraphQL, AND gRPC. Totally overkill for a startup. But hey, microservices."*

NovaTech just launched their multi-protocol API platform. REST for the normies, GraphQL for the cool kids, gRPC for the "enterprise" clients.

The docs say everything is locked down. The junior dev says "we implemented RBAC." The intern says "I tested it myself."

Can you find the hidden endpoints, chain the APIs together, and escalate your way to the flag?

## Hints

1. Not all endpoints are documented. Try looking for internal service listings.
2. GraphQL introspection might reveal more than intended.
3. Some mutations don't properly validate input fields.
4. Admin privileges unlock access to internal services.
5. gRPC reflection is your friend.

## Connection

```
http://<host>:8080
```
