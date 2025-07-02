# Voter Registry Design

Benign requests:
1. Successful voter registration.
2. Voter polling station lookup.
3. Admin logs in.
4. Admin manages polling station advisories.
5. Admin approves/rejects a registration file.

Vulnerabilities:
1. Command injection via file name parameter when registering to vote.
2. Invalid JWT signature validation.
3. Keycloak registration is allowed. Authentication on the app side checks if the user is logged in, but not if they're in the admin group.
   Solution: Disable anonymous registration OR configure app to check if user is in voter admin group.
4. Missing authorization on certain endpoints (`GET /Files/GetFile`, `POST /PollingStation/{id}/advisory`).
5. Local file inclusion on `GET /Files/GetFile` endpoint.

Twists:
1. There will be probability X that the attacker uses a User-Agent of requests, curl, etc. This can be blocked.
2. There will be probability X that the attacker's X-Forwarded-For is a known adversarial IP address. This can be blocked.

## Credentials

```
dcastell
Ic3Falcon!92

imontez
booted-unearned-entomb-backtalk-portable-jittery

jrojas
AreYouInspectingWebTrafficOrSomething?Hmmmmm

lvargas
ValV3rdeRules!

mquintero
7eVH0y*9o!B^m9OzQ3*BGs
```