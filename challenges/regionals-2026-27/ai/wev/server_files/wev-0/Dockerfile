FROM node:alpine
WORKDIR /app
COPY package-lock.json package.json ./
RUN npm ci
COPY flag.txt /flag.txt
COPY main.mjs ./
USER nobody
CMD ["node", "main.mjs"]