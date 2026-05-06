FROM node:20-bookworm-slim AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY tsconfig.json ./
COPY src ./src
RUN npm run build

FROM node:20-bookworm-slim
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --omit=dev
COPY --from=build /app/dist ./dist
ENV NODE_ENV=production
# CLI 전용 브랜치 — 컨테이너에서 예시로 도움말 실행
CMD ["node", "dist/cli.js", "--help"]
