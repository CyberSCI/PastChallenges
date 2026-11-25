FROM denoland/deno:2.9.6

WORKDIR /app

COPY --chown=deno:deno deno.json deno.lock maze.ts crypto.ts index.html ./

USER deno

RUN deno cache --frozen maze.ts

EXPOSE 8000

CMD ["run", "--frozen", "--allow-net", "--allow-read=/app/index.html", "--allow-env=flag", "maze.ts"]
