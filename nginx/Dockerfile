FROM nginx:1.27

# Копируем собранный фронтенд из образа фронта (как в Kittygram)
COPY --from=harrowsdocker/foodgram_frontend:latest /app/build /usr/share/nginx/html

# Наш конфиг nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Каталоги для статики и медиа (смонтируются как volumes)
RUN mkdir -p /var/html/static /var/html/media
