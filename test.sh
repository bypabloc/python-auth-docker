#!/bin/bash

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
COMPOSE_FILE="docker/docker-compose.test.yml"
TEST_CONTAINER="test"
PYTEST_ARGS=""

# Función para verificar si los contenedores están corriendo
check_containers_running() {
    if ! docker-compose -f $COMPOSE_FILE ps | grep -q "running"; then
        echo -e "${RED}Los contenedores de test no están corriendo. Ejecutando 'test.sh up'...${NC}"
        start_containers
    fi
}

# Función para iniciar los contenedores
start_containers() {
    echo -e "${YELLOW}Iniciando contenedores de test...${NC}"
    docker-compose -f $COMPOSE_FILE up -d

    echo -e "${YELLOW}Esperando que la base de datos esté lista...${NC}"
    sleep 5

    echo -e "${YELLOW}Aplicando migraciones...${NC}"
    docker-compose -f $COMPOSE_FILE exec -T test python manage.py migrate

    echo -e "${GREEN}Contenedores iniciados y configurados correctamente${NC}"
}

# Función para detener los contenedores
stop_containers() {
    echo -e "${YELLOW}Deteniendo contenedores de test...${NC}"
    docker-compose -f $COMPOSE_FILE down
    echo -e "${GREEN}Contenedores detenidos${NC}"
}

# Función para ejecutar los tests
run_tests() {
    local test_path=$1
    shift
    local extra_args=$@

    check_containers_running

    echo -e "${YELLOW}Ejecutando tests...${NC}"

    # Preparar comando base de pytest
    # Añadido -x --maxfail=1 para detener en el primer fallo
    local pytest_cmd="python -m pytest -v --no-header --tb=short -x --maxfail=1"

    # Agregar ruta de test si se especifica
    if [ -n "$test_path" ]; then
        pytest_cmd="$pytest_cmd $test_path"
    fi

    # Agregar argumentos extra si existen
    if [ -n "$extra_args" ]; then
        pytest_cmd="$pytest_cmd $extra_args"
    fi

    # Ejecutar los tests
    docker-compose -f $COMPOSE_FILE exec -T $TEST_CONTAINER bash -c "$pytest_cmd"

    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}Tests completados exitosamente${NC}"
    else
        echo -e "${RED}Tests fallaron${NC}"
    fi

    return $exit_code
}

# Función para mostrar ayuda
show_help() {
    echo "Uso: ./test.sh <comando> [argumentos]"
    echo ""
    echo "Comandos:"
    echo "  run [test_path] [extra_args]  Ejecutar tests (comando por defecto)"
    echo "  up                            Iniciar contenedores de test"
    echo "  down                          Detener contenedores de test"
    echo "  restart                       Reiniciar contenedores de test"
    echo "  help                          Mostrar este mensaje de ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  ./test.sh run                                    # Ejecutar todos los tests"
    echo "  ./test.sh run tests/test_login.py               # Ejecutar un archivo específico"
    echo "  ./test.sh run tests/test_login.py::TestLogin    # Ejecutar una clase específica"
    echo "  ./test.sh run -v                                # Ejecutar con output verboso"
}

# Manejo de comandos
case "${1:-run}" in
    "run")
        shift
        run_tests "$@"
        ;;
    "up")
        start_containers
        ;;
    "down")
        stop_containers
        ;;
    "restart")
        stop_containers
        start_containers
        shift
        run_tests "$@"
        ;;
    "help")
        show_help
        ;;
    *)
        echo -e "${RED}Comando no reconocido: $1${NC}"
        show_help
        exit 1
        ;;
esac
