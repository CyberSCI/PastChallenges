FROM node:lts-alpine as builder

RUN mkdir -p /verdaccio/plugins \
  && cd /verdaccio/plugins \
  && npm install --install-strategy=shallow --no-bin-links --omit=optional verdaccio-openid@latest

# 6.10
FROM docker.io/verdaccio/verdaccio@sha256:43c4067288b050422265407ea2fe747e511fcd0c407a85ec90ab9a326d9400cd

COPY --chown=$VERDACCIO_USER_UID:root --from=builder \
  /verdaccio/plugins/node_modules/verdaccio-openid \
  /verdaccio/plugins/verdaccio-openid

