FROM denoland/deno:latest

WORKDIR /app

COPY deno.json .
COPY deno.lock .
RUN deno install
COPY app.mjs .

EXPOSE 8000

CMD ["run", "--allow-net", "app.mjs"]