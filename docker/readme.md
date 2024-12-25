# Docker

Para local (con DB local) para levantar y reconstruir los contenedores:

```bash
docker-compose -f docker-compose.yml -f docker-compose.local.yml up -d --build
```

Para producción (sin DB):

```bash
# Primero configura las variables de entorno en .env.prod con los datos de tu DB externa
docker-compose up --build
```

Para local (con DB local) para levantar los contenedores (sin reconstruir):

```bash
docker-compose -f docker-compose.yml -f docker-compose.local.yml up -d
```

Si necesitas ejecutar comandos:

En local:

```bash
docker-compose -f docker-compose.yml -f docker-compose.local.yml exec web python manage.py migrate
```

En producción:

```bash
docker-compose exec web python manage.py migrate
```

Para bajar los contenedores:

```bash
docker-compose -f docker-compose.yml -f docker-compose.local.yml down -v
```
