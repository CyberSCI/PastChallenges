FROM denoland/deno:latest
WORKDIR /app
COPY deno.json .
COPY deno.lock .
RUN deno install --frozen
COPY app.ts .
CMD ["deno", "run", "--allow-env", "--allow-read=users.json,requests.json", "--allow-write=users.json,requests.json", "--allow-net=0.0.0.0:4000", "app.ts"]