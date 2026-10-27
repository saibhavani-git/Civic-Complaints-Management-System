FROM node:20-alpine

RUN apk add --no-cache curl

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY src ./src

ENV NODE_ENV=production
EXPOSE 3030

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://127.0.0.1:3030/health || exit 1

CMD ["node", "src/index.js"]
