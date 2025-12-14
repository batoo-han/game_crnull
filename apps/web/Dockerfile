FROM node:22-alpine AS build

WORKDIR /repo

# Устанавливаем зависимости
COPY apps/web/package.json /repo/apps/web/package.json
COPY apps/web/package-lock.json /repo/apps/web/package-lock.json

WORKDIR /repo/apps/web
RUN npm ci --no-fund --no-audit

# Копируем исходники и собираем
COPY apps/web /repo/apps/web
RUN npm run build


FROM nginx:1.27-alpine AS runtime

# SPA + прокси на backend (/api -> api:8000)
COPY infra/nginx/web.conf /etc/nginx/conf.d/default.conf

COPY --from=build /repo/apps/web/dist /usr/share/nginx/html

EXPOSE 80


