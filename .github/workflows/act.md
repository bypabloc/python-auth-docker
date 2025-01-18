# Act

## Install

```bash
curl -L https://github.com/nektos/act/releases/download/v0.2.61/act_Linux_x86_64.tar.gz -o act.tar.gz
tar xzvf act.tar.gz
sudo mv act /usr/local/bin/
sudo chmod +x /usr/local/bin/act
```

## Version

```bash
act --version
```

## Usage

```bash
act
```

Seleccionar un evento específico: Si tienes un archivo JSON que simula un evento de GitHub (por ejemplo, push), puedes usarlo con:

```bash
act push -e path/to/event.json
```

```bash
act push -j build -W .github/workflows/merge-dev.yml -s GITHUB_TOKEN=""
```

Si quieres reconstruir la imagen

```bash
act push --rebuild
```

Seleccionar un runner específico: act por defecto usa una imagen de Docker que simula el entorno de GitHub Actions. Puedes especificar una imagen diferente si lo necesitas:

```bash
act -P ubuntu-latest=ghcr.io/catthehacker/ubuntu:full-latest
```

Ejecutar un workflow específico: Si quieres ejecutar un workflow específico por su nombre:

```bash
act -W .github/workflows/merge-dev.yml
```

Si tu workflow necesita secretos, puedes pasarlos a act usando el parámetro --secret, por ejemplo:

```bash
act --secret MY_SECRET=value
```

Las credenciales de GitHub se pueden pasar a act usando el parámetro --secret, por ejemplo:

```bash
ASTRO_STUDIO_APP_TOKEN=<token>
PORT=4321
BASE_URL=http://localhost:4321
```

Comando completo:

```bash
act push -P ubuntu-latest=ghcr.io/catthehacker/ubuntu:full-latest --action-offline-mode -j build -W .github/workflows/ci.yml --secret-file .github/workflows/.secrets
```

```bash
docker rmi $(docker images 'catthehacker/ubuntu*' -q) -f
```
