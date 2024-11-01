Пока админ заведен как
user: ss_admin
password: ss_admin

Создание PostgreSQL БД
CREATE DATABASE sitesoft_parcer;
CREATE USER sitesoftadmin WITH PASSWORD 'admin';
ALTER ROLE sitesoftadmin SET client_encoding TO 'utf8';
ALTER ROLE sitesoftadmin SET timezone TO 'UTC';
ALTER ROLE sitesoftadmin SET default_transaction_isolation TO 'read committed';
ALTER USER sitesoftadmin CREATEDB;
ALTER DATABASE sitesoft_parcer OWNER TO sitesoftadmin;
ALTER SCHEMA public OWNER TO sitesoftadmin;
GRANT ALL PRIVILEGES ON DATABASE sitesoft_parcer TO sitesoftadmin;
