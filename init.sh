#!/bin/bash

# Файл конфигурации
CONFIG_FILE="parcer_app/config.json"
ENV_FILE="parcer_app/.env"
INITIAL_DATA="parcer_app/initial_data.json"

# ПИДы для фоновых процессов
REDIS_PID=""
CELERY_PID=""
RUNSERVER_PID=""
PARCER_PID=""

# Функция для очистки (остановка процессов)
cleanup() {
    if [ -n "$REDIS_PID" ]; then
        kill "$REDIS_PID" 2>/dev/null
        echo "Redis остановлен."
    fi
    if [ -n "$CELERY_PID" ]; then
        kill "$CELERY_PID" 2>/dev/null
        echo "Celery остановлен."
    fi
    if [ -n "$RUNSERVER_PID" ]; then
        kill "$RUNSERVER_PID" 2>/dev/null
        echo "Django сервер остановлен."
    fi
    if [ -n "$PARCER_PID" ]; then
        kill "$PARCER_PID" 2>/dev/null
        echo "Парсер остановлен."
    fi
}

# Функция для обработки ошибок
handle_error() {
    echo "ОШИБКА: что-то пошло не так. Отмена изменений."

    if [ -f ".env.bak" ]; then
        mv .env.bak .env
        echo ".env восстановлен из резервной копии."
    fi

    exit 1
}

# Функция для восстановления .env
restore_env() {
    if [ -f "$ENV_FILE.bak" ]; then
        mv "$ENV_FILE.bak" "$ENV_FILE"
        echo ".env восстановлен из резервной копии."
    fi
}

# Установка обработчика ошибок
trap 'handle_error' ERR
trap restore_env EXIT INT TERM
trap 'echo -e "\nОШИБКА: Сценарий был прерван. Завершение работы."; exit 1' INT
trap 'cleanup; exit' EXIT INT TERM

# Функция для загрузки конфигурации
load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        DATABASE_NAME=$(jq -r '.DATABASE_NAME' "$CONFIG_FILE")
        DATABASE_USER=$(jq -r '.DATABASE_USER' "$CONFIG_FILE")
        DATABASE_PASSWORD=$(jq -r '.DATABASE_PASSWORD' "$CONFIG_FILE")
        DATABASE_HOST=$(jq -r '.DATABASE_HOST' "$CONFIG_FILE")
        DATABASE_PORT=$(jq -r '.DATABASE_PORT' "$CONFIG_FILE")
        SUPERUSER_NAME=$(jq -r '.SUPERUSER_NAME' "$CONFIG_FILE")
        SUPERUSER_EMAIL=$(jq -r '.SUPERUSER_EMAIL' "$CONFIG_FILE")
        SUPERUSER_PASSWORD=$(jq -r '.SUPERUSER_PASSWORD' "$CONFIG_FILE")
        return 0
    else
        while true; do
            echo "Конфигурационный файл не найден. Создать?"
            read -p "(y/n): " CHOICE
        
            case $CHOICE in
                y)
                    create_default_config
                    break
                    ;;
                n)
                    echo "Отмена. Завершение скрипта."
                    exit 1
                    ;;
                *)
                    echo "Неверный выбор. Пожалуйста, попробуйте еще раз."
                    ;;
            esac
        done
    fi
}

# Функция для создания конфигурационного файла с настройками по умолчанию
create_default_config() {
    request_db_credentials
    save_config
}

# Функция для сохранения конфигурации
save_config() {
    cat << EOF > "$CONFIG_FILE"
{
    "DATABASE_NAME": "$DATABASE_NAME",
    "DATABASE_USER": "$DATABASE_USER",
    "DATABASE_PASSWORD": "$DATABASE_PASSWORD",
    "DATABASE_HOST": "$DATABASE_HOST",
    "DATABASE_PORT": "$DATABASE_PORT",
    "SUPERUSER_NAME": "$SUPERUSER_NAME",
    "SUPERUSER_EMAIL": "$SUPERUSER_EMAIL",
    "SUPERUSER_PASSWORD": "$SUPERUSER_PASSWORD"
}
EOF
}

# Функция для проверки согласованности конфигурации
check_consistency() {
    if [ -f "$ENV_FILE" ]; then
        ENV_DATABASE_NAME=$(grep 'DATABASE_NAME=' "$ENV_FILE" | cut -d '=' -f 2 | tr -d "'\" ")
        ENV_DATABASE_USER=$(grep 'DATABASE_USER=' "$ENV_FILE" | cut -d '=' -f 2 | tr -d "'\" ")
        ENV_DATABASE_HOST=$(grep 'DATABASE_HOST=' "$ENV_FILE" | cut -d '=' -f 2 | tr -d "'\" ")
        ENV_DATABASE_PORT=$(grep 'DATABASE_PORT=' "$ENV_FILE" | cut -d '=' -f 2 | tr -d "'\" ")

        ENV_SUPERUSER_NAME=$(grep 'SUPERUSER_NAME=' "$ENV_FILE" | cut -d '=' -f 2 | tr -d "'\" ")
        

        if [[ "$DATABASE_NAME" != "$ENV_DATABASE_NAME" || "$DATABASE_USER" != "$ENV_DATABASE_USER" || "$SUPERUSER_NAME" != "$ENV_SUPERUSER_NAME" || "$DATABASE_HOST" != "$ENV_DATABASE_HOST" || "$DATABASE_PORT" != "$ENV_DATABASE_PORT" ]]; then
            echo "Предупреждение: настройки в .env и конфигурационном файле не совпадают."
            return 1
        fi
    fi
    return 0
}

# Функция для запроса данных подключения к БД
request_db_credentials() {
    echo "Ввод данных подключения к базе данных."
    read -p "Введите имя базы данных: " DATABASE_NAME
    read -p "Введите имя пользователя базы данных: " DATABASE_USER
    read -sp "Введите пароль базы данных: " DATABASE_PASSWORD
    echo ""

    # Валидация хоста
    read -p "Введите хост базы данных (по умолчанию 'localhost'): " DATABASE_HOST
    DATABASE_HOST=${DATABASE_HOST:-localhost}
    
    # Валидация порта
    while true; do
        read -p "Введите порт базы данных (по умолчанию '5432'): " DATABASE_PORT
        DATABASE_PORT=${DATABASE_PORT:-5432}

        if [[ "$DATABASE_PORT" =~ ^[0-9]{4}$ ]]; then
            break
        else
            echo "ОШИБКА: Порт должен быть числом, состоящим из 4 цифр. Попробуйте снова."
        fi
    done
}

# Проверка наличия виртуального окружения
if [ ! -d ".venv" ]; then
    while true; do
        echo "ОШИБКА: виртуальное окружение не найдено. Создать?"
        read -p "(y/n): " CHOICE

        case $CHOICE in
            y)
                python3 -m venv .venv
                if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
                    source ./.venv/Scripts/activate
                else
                    source .venv/bin/activate
                fi
                echo "Виртуальное окружение создано."
                break
                ;;
            n)
                echo "Отмена. Завершение скрипта."
                exit 1
                ;;
            *)
                echo "Неверный выбор. Пожалуйста, попробуйте еще раз."
                ;;
        esac
    done
else
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        source ./.venv/Scripts/activate
    else
        source .venv/bin/activate
    fi
    echo "Виртуальное окружение активировано."
fi

# Проверка установленных зависимостей
if [ -f "req.txt" ]; then
    echo "Проверка установленных зависимостей..."
    # Сравниваем установленные пакеты с требуемыми
    MISSING_PACKAGES=$(python -m pip install --dry-run -r requirements.txt 2>&1 | grep -i "would install" | awk '{print $4}')

    if [ -n "$MISSING_PACKAGES" ]; then
        echo "Найдены отсутствующие зависимости:"
        echo "$MISSING_PACKAGES"
        while true; do
            echo "Установить отсутствующие зависимости?"
            read -p "(y/n): " INSTALL_CHOICE

            case $INSTALL_CHOICE in
                y)
                    echo "Устанавливаю зависимости..."
                    python -m pip install -r requirements.txt
                    echo "Зависимости установлены."
                    break
                    ;;
                n)
                    echo "Отмена. Завершение скрипта. Установите зависимости вручную."
                    exit 1
                    ;;
                *)
                    echo "Неверный выбор. Пожалуйста, попробуйте еще раз."
                    ;;
            esac
        done
    else
        echo "Все зависимости установлены."
    fi
else
    echo "ОШИБКА: файл req.txt не найден. Завершение скрипта."
    exit 1
fi

# Проверка наличия .env файла
if [ ! -f "$ENV_FILE" ]; then
    echo "ОШИБКА: файл .env не найден. Завершение скрипта."
    exit 1
fi

# Проверка наличия .env файла и создание резервной копии при необходимости
if [ -f "$ENV_FILE" ]; then
    cp "$ENV_FILE" "$ENV_FILE.bak"
    echo "Создана резервная копия .env в .env.bak."
fi

# Проверка наличия initial_data.json
if [ ! -f "$INITIAL_DATA" ]; then
    echo "ОШИБКА: файл initial_data.json не найден. Завершение скрипта."
    exit 1
fi

# Загружаем конфигурацию
load_config

# Если конфигурация загружена
if [ $? -eq 0 ]; then
    echo "Конфигурация загружена. Текущие настройки:"
    echo "Имя базы данных: $DATABASE_NAME"
    echo "Имя пользователя базы данных: $DATABASE_USER"
    echo "Пароль базы данных: (заполнен)"
    echo "Хост базы данных: $DATABASE_HOST"
    echo "Порт базы данных: $DATABASE_PORT"
    echo "Имя суперпользователя: $SUPERUSER_NAME"

    # Интерактивный выбор
    while true; do
        echo "Выберите действие:"
        echo "1) Использовать старые настройки"
        echo "2) Изменить настройки"
        read -p "(1/2): " CHOICE
        
        case $CHOICE in
            1)
                break
                ;;
            2)
                request_db_credentials
                break
                ;;
            *)
                echo "Неверный выбор. Пожалуйста, попробуйте еще раз."
                ;;
        esac
    done
else
    request_db_credentials
fi

# Проверяем подключение к базе данных
echo "Проверяем подключение к базе данных..."
if ! python manage.py parcer_app.tests.test_check_database; then
    echo "ОШИБКА: Подключение к базе данных не удалось. Завершение скрипта."
    restore_env
    exit 1
fi

# Проверка согласованности конфигурации
if ! check_consistency; then
    echo "Конфигурация и .env не совпадают. Запрашиваем новые настройки."
    request_db_credentials
fi

# Записываем данные подключения к базе данных в .env
{
    echo "DATABASE_ENGINE='django.db.backends.postgresql'"
    echo "DATABASE_NAME='$DATABASE_NAME'"
    echo "DATABASE_USER='$DATABASE_USER'"
    echo "DATABASE_PASSWORD='$DATABASE_PASSWORD'"
    echo "DATABASE_HOST='$DATABASE_HOST'"
    echo "DATABASE_PORT='$DATABASE_PORT'"
} > "$ENV_FILE"

# Обновляем резервную копию .env.bak после успешного изменения .env
cp "$ENV_FILE" "$ENV_FILE.bak"

# Выполняем миграции
echo "Применяем миграции..."
python manage.py makemigrations
python manage.py migrate

# Проверка загрузки начальных данных
echo "Проверка загрузки начальных данных..."
if ! python manage.py parcer_app.tests.test_load_initial_data; then
    echo "ОШИБКА: Загрузка начальных данных не удалась. Завершение скрипта."
    restore_env
    exit 1
fi


# Запрашиваем данные суперпользователя
if [[ -z "$SUPERUSER_NAME" ]]; then
    read -p "Введите имя суперпользователя: " SUPERUSER_NAME
    read -p "Введите email суперпользователя: " SUPERUSER_EMAIL
    read -sp "Введите пароль суперпользователя: " SUPERUSER_PASSWORD
    echo ""

    # Сохранить конфигурацию
    save_config
fi

# Проверка существования суперпользователя
if python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print(User.objects.filter(username='$SUPERUSER_NAME').exists())" | grep -q True; then
    echo "Суперпользователь '$SUPERUSER_NAME' уже существует."
else
    echo "Создаем суперпользователя..."
    echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('$SUPERUSER_NAME', '$SUPERUSER_EMAIL', '$SUPERUSER_PASSWORD')" | python manage.py shell
fi

# Загружаем начальные данные
echo "Загружаем начальные данные..."
python manage.py load_initial_data

echo "Инициализация завершена."

# Запуск Redis
echo "Запускаем Redis..."
redis-server &
REDIS_PID=$!
if [ $? -ne 0 ]; then
    echo "ОШИБКА: Не удалось запустить Redis."
    exit 1
fi

# Запуск Celery
echo "Запускаем Celery..."
elery -A config worker -l info -P solo &
CELERY_PID=$!
if [ $? -ne 0 ]; then
    echo "ОШИБКА: Не удалось запустить Celery."
    exit 1
fi

# Проверка работы парсера
echo "Проверка работы парсера..."
if ! python manage.py parcer_app.tests.fetch_articles; then
    echo "ОШИБКА: Ошибка работы парсера. Завершение скрипта."
    restore_env
    exit 1
fi

# Запускаем сервер
echo "Запускаем сервер..."
python manage.py runserver
RUNSERVER_PID=$!

echo "Запускаем парсер..."
python manage.py parcer_app.tasks.schedule_fetching
PARCER_PID=$!

# Ожидание завершения процесса сервера
wait "$RUNSERVER_PID"

# После завершения работы сервера очищаем
cleanup
