import unittest
import src.db_info as db_info
import src.db_helper as db_helper
import json

class Test(unittest.TestCase):
    def test_UsersColumns(self):
        with open("test/data/Users_columns.json", "r") as f:
            expected_columns = json.load(f)
        actual_columns = db_info.get_column_names(db_helper.create_default_engine(), "Users")
        self.assertSetEqual(set(expected_columns), set(actual_columns), f"All columns in the User table should exist")

    def test_AllTables(self):
        with open("test/data/all_tables.json", "r") as f:
            expected_tables = json.load(f)
        actual_tables = db_info.get_all_table_names(db_helper.create_default_engine())
        self.assertSetEqual(set(expected_tables), set(actual_tables), f"All tables should exist")

    def test_Tables(self):
        with open("test/data/base_tables.json", "r") as f:
            expected_tables = json.load(f)
        actual_tables = db_info.get_table_names(db_helper.create_default_engine())
        self.assertSetEqual(set(expected_tables), set(actual_tables), f"All base tables should exist")