# use the official Bun image
# see all versions at https://hub.docker.com/r/oven/bun/tags
FROM node:20-slim AS base
WORKDIR /usr/src/app

ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable

ARG POSTGRES_URL
ENV POSTGRES_URL=${POSTGRES_URL}

# install dependencies into temp directory
# this will cache them and speed up future builds
FROM base AS build
COPY package.json pnpm-lock.yaml ./

RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --frozen-lockfile

COPY . .
RUN pnpm run build

# copy production dependencies and source code into final image
FROM base AS release
COPY --from=build /usr/src/app/ .
COPY docker-entrypoint.sh ./

# run the app
ENTRYPOINT [ "/usr/src/app/docker-entrypoint.sh" ]
