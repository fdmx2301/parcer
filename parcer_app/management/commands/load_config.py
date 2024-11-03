import json
import sys

def load_config(config_file):
    try:
        with open(config_file, 'r') as file:
            config = json.load(file)
        
        print(config.get("DATABASE_NAME", ""))
        print(config.get("DATABASE_USER", ""))
        print(config.get("DATABASE_PASSWORD", ""))
        print(config.get("DATABASE_HOST", ""))
        print(config.get("DATABASE_PORT", ""))
        print(config.get("SUPERUSER_NAME", ""))
        print(config.get("SUPERUSER_EMAIL", ""))
        print(config.get("SUPERUSER_PASSWORD", ""))
    except Exception as e:
        print(f"ОШИБКА: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(1)

    load_config(sys.argv[1])
