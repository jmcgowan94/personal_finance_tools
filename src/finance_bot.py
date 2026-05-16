import json
import math
import os
from pathlib import Path
import sqlite3
import sys

import questionary

from sys_config import SYS_DELIMITERS

class FinanceBot:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.user_dir_path = self.project_root / "user_data"
        self.user_config_path = self.user_dir_path / "user_config.json"
        self.user_config = None
        self.working_dir = None
        self.statements_dir = None
        self.db_path = None
        self.processed_files = None
        self.initialize()

    def initialize(self):
        self.print_header("Initializing", 100)
        total_steps = 3
        current_step = 1
        print(f"\n---- Validating User Config ({current_step}/{total_steps}) ----")
        self.user_dir_path.mkdir(parents=True, exist_ok=True)
        self.user_config = self.set_user_config()
        current_step += 1
        print("Complete.")
        print(f"\n---- Validating Working Directory ({current_step}/{total_steps}) ----")
        self.working_dir = self.check_directory(Path.home(), "working_dir")
        print(f"Selected Working Directory: {self.working_dir}")
        current_step += 1
        print("Complete.")
        print(f"\n---- Validating Database ({current_step}/{total_steps}) ----")
        self.validate_database()
        current_step += 1
        print("Complete.")

    def print_header(self, text, char_num):
        act_char_num = char_num - 2
        num_dashes = math.floor((act_char_num - len(text))/2)
        print(f"\n{'-' * num_dashes} {text} {'-' * num_dashes}")

    def set_user_config(self):
        if not self.user_config_path.exists():
            with self.user_config_path.open(mode="w") as f:
                json.dump({}, f)
        with self.user_config_path.open(mode="r") as f:
            config = json.load(f)
        return config

    def get_user_config_value(self, key, default=None):
        return self.user_config.get(key, default)

    def set_user_config_value(self, key, value):
        self.user_config[key] = value
        with self.user_config_path.open(mode="w") as f:
            json.dump(self.user_config, f, indent=2)

    def check_directory(self, starting_dir, dir_nam):
        selected_dir = self.get_user_config_value(dir_nam)
        if selected_dir is None:
            selected_dir = self.set_directory(starting_dir)
            self.set_user_config_value(dir_nam, f"{selected_dir}")
        else:
            user_answer = questionary.select(
                f"Previous Directory: {selected_dir}\n"
                f"  Would you like to use the same directory?:",
                choices=["YES", "NO", "EXIT"]
            ).ask()
            if user_answer == "EXIT":
                print("Exiting script.\n")
                sys.exit()
            elif user_answer == "NO":
                selected_dir = self.set_directory(starting_dir)
                self.set_user_config_value(dir_nam, f"{selected_dir}")
            else:
                pass
        return selected_dir

    def set_directory(self, starting_dir):
        current_dir = Path(starting_dir)
        while True:
            folders = os.listdir(current_dir)
            options = []
            for item in folders:
                item_path = current_dir / item
                if item_path.is_dir() and os.access(item_path, os.R_OK | os.W_OK | os.X_OK):
                    options.append(item)
            options = [i for i in options if i[0] != "."]
            options.sort()
            options.insert(0, "DONE")
            options.append("BACK")
            options.append("EXIT")
            print("")
            user_input = questionary.select(
                f"Current filepath: {current_dir}\n  Continue navigating, or choose 'DONE':",
                choices=options
            ).ask()
            if user_input == "EXIT" or user_input is None:
                print("Exiting script.\n")
                sys.exit()
            elif user_input == "DONE":
                return current_dir
            elif user_input == "BACK":
                if current_dir == starting_dir:
                    print("Already at the starting directory.")
                else:
                    current_dir = current_dir.parent
            else:
                current_dir = current_dir / user_input

    def validate_database(self):
        self.db_path = self.user_dir_path / "data.db"
        existed = self.db_path.exists()
        sqlite3.connect(self.db_path)
        print(f"{'Validated' if existed else 'Created'} database at: {self.db_path}")

    def import_new_data(self):
        self.print_header("Importing Data", 100)
        total_steps = 3
        current_step = 1
        print(f"\n---- Connecting to database ({current_step}/{total_steps}) ----")
        self.validate_transactions_raw()
        current_step += 1
        print("Complete.")
        print(f"\n---- Checking for statements ({current_step}/{total_steps}) ----")
        self.check_directory(self.working_dir, "statements_dir")
        current_step += 1
        print("Complete.")

    def validate_transactions_raw(self):
        table_name = "transactions_raw"
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(f"""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='{table_name}'
                """)
        table_exists = cursor.fetchone() is not None
        if table_exists:
            pass
        else:
            conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        source_file TEXT NOT NULL,
                        cred_or_debit TEXT NOT NULL,
                        posting_date TEXT NOT NULL,
                        description TEXT NOT NULL,
                        type TEXT NOT NULL,
                        check_slip_no TEXT,
                        amount REAL NOT NULL,
                        balance REAL NOT NULL
                    )
            """)
            conn.commit()
            conn.close()
        print(f"{'Validated' if table_exists else 'Created'} table: {table_name}")

    def get_processed_files(self):
        processed_files = self.get_user_config_value("processed_files")
        if processed_files is None:
            processed_files = []
            self.set_user_config_value("processed_files", processed_files)
        return processed_files

    def check_for_new_files(self):
        files = os.listdir(self.statements_dir)
        for f in sorted(files):
            if f.lower() not in self.processed_files:
                user_import = questionary.select(
                    f"Import file: {f}?:",
                    choices=["YES", "NO", "EXIT"]
                ).ask()
                if user_import == "EXIT":
                    print("Exiting script.\n")
                    sys.exit()
                elif user_import == "YES":
                    self.import_file(f)

    def import_files(self, filename):
        print(f"Importing: {filename}")

    def detect_delimiter(self, lines):
        counts = {d: sum(line.count(d) for line in lines) for d in SYS_DELIMITERS}
        best = max(counts, key=counts.get)
        # If we found zero delimiters for every candidate, don't guess incorrectly
        if counts[best] == 0:
            raise ValueError(f"Could not detect delimiter from sample. Counts={counts}")
        return best
