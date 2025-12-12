FROM node:18-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM alpine:3.20
WORKDIR /app

COPY --from=build /app/build /app/build

CMD sh -c "rm -rf /frontend/* && cp -r /app/build/* /frontend/"
