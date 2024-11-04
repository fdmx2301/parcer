import json
import sys

def load_config(config_file):
    try:
        with open(config_file, 'r', encoding='utf-8') as file:
            config = json.load(file)

            required_keys = ["DATABASE_NAME", "DATABASE_USER", "DATABASE_PASSWORD", "DATABASE_HOST", "DATABASE_PORT", "SUPERUSER_NAME", "SUPERUSER_EMAIL", "SUPERUSER_PASSWORD"]
            for key in required_keys:
                if key not in config:
                    print(f"Ошибка: ключ '{key}' отсутствует в конфигурации", file=sys.stderr)
                    sys.exit(1)

            # Заменяем пустые строки на 'EMPTY_STRING'
            return tuple(value if value != "" else 'EMPTY_STRING' for value in (
                config["DATABASE_NAME"],
                config["DATABASE_USER"],
                config["DATABASE_PASSWORD"],
                config["DATABASE_HOST"],
                config["DATABASE_PORT"],
                config["SUPERUSER_NAME"],
                config["SUPERUSER_EMAIL"],
                config["SUPERUSER_PASSWORD"]
            ))
    except Exception as e:
        print(f"ОШИБКА: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(1)

    config_values = load_config(sys.argv[1])
    
    print(" ".join(str(value) for value in config_values))
