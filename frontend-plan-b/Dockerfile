FROM node:24-alpine AS build

WORKDIR /app

ARG VITE_API_BASE_URL=http://localhost:8000
ARG VITE_WS_BASE_URL=ws://localhost:8000

ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_WS_BASE_URL=${VITE_WS_BASE_URL}

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.29-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
