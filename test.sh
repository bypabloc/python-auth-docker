#!/bin/bash

set -e

# Constantes
DOCKER_COMPOSE="docker-compose -f docker/docker-compose.test.yml"
CONTAINER_NAME="python_auth_test"

# Función para verificar si los contenedores están corriendo
check_containers() {
    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo "Starting test containers..."
        $DOCKER_COMPOSE up -d

        # Wait for containers to be ready
        echo "Waiting for containers to be ready..."
        while ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; do
            sleep 1
        done

        echo "Running migrations..."
        docker exec ${CONTAINER_NAME} python manage.py migrate
    fi
}

# Función para ejecutar los tests
run_tests() {
    local test_path=$1
    local extra_args=${@:2}

    if [ -z "$test_path" ]; then
        echo "Running all tests..."
        docker exec ${CONTAINER_NAME} pytest -v
    else
        echo "Running tests in $test_path..."
        docker exec ${CONTAINER_NAME} pytest $test_path -v $extra_args
    fi
}

# Función para detener los contenedores
stop_containers() {
    echo "Stopping test containers..."
    $DOCKER_COMPOSE down -v
}

# Función para mostrar la ayuda
show_help() {
    echo "Usage: ./test.sh [command] [test_path] [extra_args]"
    echo
    echo "Commands:"
    echo "  run [test_path]    Run tests (default command)"
    echo "  up                 Start test containers"
    echo "  down               Stop test containers"
    echo "  restart            Restart test containers"
    echo
    echo "Examples:"
    echo "  ./test.sh run                                  # Run all tests"
    echo "  ./test.sh run tests/test_login.py             # Run specific test file"
    echo "  ./test.sh run tests/test_login.py -k test_name # Run specific test"
    echo "  ./test.sh down                                # Stop containers"
}

# Procesar comandos
case "$1" in
    "help"|"-h"|"--help")
        show_help
        exit 0
        ;;
    "up")
        check_containers
        ;;
    "down")
        stop_containers
        ;;
    "restart")
        stop_containers
        check_containers
        ;;
    "run"|"")
        check_containers
        run_tests "${@:2}"
        ;;
    *)
        check_containers
        run_tests "$@"
        ;;
esac
