## References

- https://dev.to/ciscoemerge/cicd-access-all-areas-g1e
- https://www.hackthebox.com/blog/cve-2024-23897
- https://ctftime.org/writeup/36960

## Vulnerabilities

1. Jenkins config file in publicly accessible S3 bucket
2. Logged in users in Jenkins have write access to pipelines
3. Users can sign up to the CI/CD instance
4. Shell injection in one of the pipelines
5. AWS Access keys in shared creds file, can write docker images
6. Exposed docker socket

## Applications

1. Canary -- basic Python application

## To-Do

- [ ] Confirm deployment pipelines work
- [ ] Confirm system runs and can build projects
- [ ] Make pipeline with a shell injection vuln
- [ ] Write attacker scripts
  - [ ] Config file in bucket
  - [ ] Write access
  - [ ] User signup
  - [ ] Shell injection
  - [ ] AWS Access keys
  - [ ] Docker socket
