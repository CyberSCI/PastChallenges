FROM node:22-bookworm-slim

ENV NODE_ENV=production \
    PORT=80 \
    DATABASE_PATH=/var/lib/controller/ships.sqlite

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --omit=dev --no-audit --no-fund

COPY src ./src

RUN mkdir -p /var/lib/controller \
    && chown -R node:node /app /var/lib/controller

USER node

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=3s --retries=5 --start-period=10s \
    CMD node -e "fetch('http://127.0.0.1:80/healthz').then((response) => process.exit(response.ok ? 0 : 1)).catch(() => process.exit(1))"

CMD ["node", "src/server.js"]