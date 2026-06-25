# Shellnet

> What I had in mind was a "login hardening application" that sanitizes username and password before invoking telnet on your behalf. For username it would check that there are no spaces in the username and that the username does not match regex "root$".
> Both of these restrictions could then be bypassed by supplying username `-f${IFS:0:1}root${IFS:0:1}`
> There could be other tricks too.

## References

- [Finger Protocol](https://www.bleepingcomputer.com/news/security/decades-old-finger-protocol-abused-in-clickfix-malware-attacks/)
- [CVE](https://www.cve.org/CVERecord?id=CVE-2026-24061)

## Vuln Chain
