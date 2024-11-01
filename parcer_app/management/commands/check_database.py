from django.db import connections
from django.db.utils import OperationalError

class DatabaseChecker:
    def __init__(self):
        self.connection = connections['default']

    def check_connection(self):
        try:
            self.connection.ensure_connection()
            return True
        except OperationalError:
            print(f"ОШИБКА: Не удалось подключиться к базе данных")
            return False

    def create_test_table(self):
        with self.connection.cursor() as cursor:
            cursor.execute(""" 
                CREATE TABLE IF NOT EXISTS test_table (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL
                )
            """)

    def run_select_query(self):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT * FROM test_table;")
            results = cursor.fetchall()
            return results

    def perform_action(self, action):
        if action == "check_connection":
            return self.check_connection()
        elif action == "create_table":
            self.create_test_table()
        elif action == "run_select_query":
            return self.run_select_query()
        else:
            raise ValueError(f"Неизвестное действие: {action}")
