from django.test import TestCase
from django.core.management import call_command
from django.db import connection
from parcer_app.management.commands.check_database import DatabaseChecker

class DatabaseCheckerTest(TestCase):
    
    def setUp(self):
        self.db_checker = DatabaseChecker()

    def test_connection(self):
        self.assertTrue(self.db_checker.perform_action("check_connection"))

    def test_create_table(self):
        self.db_checker.perform_action("create_table")
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM test_table;")
            result = cursor.fetchall()
            self.assertIsNotNone(result)

    def test_select_query(self):
        self.db_checker.perform_action("create_table")
        self.db_checker.perform_action("run_select_query")
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM test_table;")
            result = cursor.fetchall()
            self.assertIsNotNone(result)
