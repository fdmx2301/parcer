# SITESOFT PARCER

## Требования

- **Операционная система:** Windows с установленным WSL (Windows Subsystem for Linux)
- **Дистрибутив:** Ubuntu 20.04
- **Redis:** Установленный и запущенный Redis-сервер

## Установка

1. Убедитесь, что у вас установлен WSL и настроен дистрибутив Ubuntu 20.04. Если WSL еще не установлен, выполните следующие шаги:
   - Откройте PowerShell от имени администратора и выполните:
    ```bash
     wsl --install
     ```
     либо:
     ```bash
     wsl --install -d Ubuntu
     ```
   - После установки перезагрузите компьютер и завершите настройку Ubuntu.

2. Установите Redis:
   - Откройте терминал Ubuntu и выполните следующие команды для установки Redis:
     ```bash
     sudo apt update
     sudo apt install redis-server
     ```
   - После установки запустите Redis-сервер:
     ```bash
     sudo service redis-server start
     ```
     либо просто
     ```bash
     redis-server
     ```

## Запуск приложения

1. Откройте Bash-терминал в корне папки с вашим проектом. (либо в bash терминале укажите путь до скрипта)
2. Запустите скрипт:
   ```bash
   ./init.sh
   ```
3. Следуйте инструкциям в терминале:
    3.1. Будет предложено установить .venv (виртуальное окружение)
    3.2. Будет предложено установить зависимости из req.txt (можете установить их вручную):
    ```bash
    pip install -r req.txt
    ```
    3.3. Подключитесь к вашей базе данных, убедитесь что у пользователя достаточно прав, пример:
    ```sql
    CREATE DATABASE sitesoft_parcer;
    CREATE USER sitesoftadmin WITH PASSWORD 'admin';
    ALTER ROLE sitesoftadmin SET client_encoding TO 'utf8';
    ALTER ROLE sitesoftadmin SET timezone TO 'UTC';
    ALTER ROLE sitesoftadmin SET default_transaction_isolation TO 'read committed';
    ALTER USER sitesoftadmin CREATEDB;
    ALTER DATABASE sitesoft_parcer OWNER TO sitesoftadmin;
    ALTER SCHEMA public OWNER TO sitesoftadmin;
    GRANT ALL PRIVILEGES ON DATABASE sitesoft_parcer TO sitesoftadmin;
    ```
    3.4. Введите данные пользователя для админ панели Django

## Комментарии
1) Программа использует админ панель только для просмотра, ввиду того что таблицы и начальные
данные автоматически создают/добавляются из initial_data.json // В будущем стоит пофиксить (например
добавить проверку на первоначальную загрузку данных из файла)
2) По хорошему не стоило бы добавлять .env в репо, данные о БД можно складировать в config.json
и оттуда же подтягивать в settings.py // В будущем стоит исправить
3) Удаление ключевых файлов таких как .env и/или initial_data.json бесповоротно сломают программу,
попытки редактирования БД через терминал Postgres а не через ORM приведут к аналогичному результату
4) В будущем стоит добавить больше тестов
5) Docker конфигурация пока не тестировалось и ее нет в репо