import json
import os
from pathlib import Path
import sqlite3
import sys

import questionary

from sys_config import SYS_DELIMITERS

class FinanceBot:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.user_config = None
        self.working_dir = None
        self.data = None
        self.processed_files = None
        self.initialize()

    def initialize(self):
        print("\n-- Initializing --")
        total_steps = 3
        current_step = 1
        print(f"\n-- ({current_step}/{total_steps}) Setting user config --")
        self.user_config = self.set_user_config()
        current_step += 1
        print("Complete.")
        print(f"\n-- ({current_step}/{total_steps}) Setting working directory --")
        self.working_dir = self.get_working_dir()
        print(f"Selected Working Directory: {self.working_dir}")
        current_step += 1
        print("Complete.")
        print(f"\n-- ({current_step}/{total_steps}) Validating database --")
        self.data = self.validate_database()
        current_step += 1
        print("Complete.")

    def set_user_config(self):
        project_root = self.project_root
        private_dir = project_root / "private"
        private_dir.mkdir(exist_ok=True)
        config_file = private_dir / "user_config.json"
        if not config_file.exists():
            with config_file.open(mode="w") as f:
                json.dump({}, f)
        with config_file.open(mode="r") as f:
            config = json.load(f)
        return config

    def get_user_config_value(self, key):
        if key not in self.user_config:
            self.user_config[key] = None
        return self.user_config[key]

    def set_user_config_value(self, key, value):
        self.user_config[key] = value
        user_config_path = self.project_root / "private" / "user_config.json"
        with user_config_path.open(mode="w") as f:
            json.dump(self.user_config, f, indent=2)

    def get_working_dir(self):
        working_dir = self.get_user_config_value("working_dir")
        if working_dir is None:
            working_dir = self.set_directory(Path.home())
            self.set_user_config_value("working_dir", f"{working_dir}")
        else:
            user_answer = questionary.select(
                f"Previous Working Directory: {working_dir}\n"
                f"  Would you like to use the same working directory?:",
                choices=["YES", "NO", "EXIT"]
            ).ask()
            if user_answer == "EXIT":
                print("Exiting script.\n")
                sys.exit()
            elif user_answer == "NO":
                working_dir = self.set_directory(Path.home())
                self.set_user_config_value("working_dir", f"{working_dir}")
            else:
                pass
        return working_dir

    def set_directory(self, starting_dir):
        current_dir = starting_dir
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
        data_dir = self.project_root / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        db_path = data_dir / "data.db"
        existed = db_path.exists()
        conn = sqlite3.connect(db_path)
        print(f"{'Validated' if existed else 'Created'} database at: {db_path}")
        return conn

    def validate_transactions_raw(self):
        conn = sqlite3.connect(self.data)
        conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions_raw (
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

    def get_processed_files(self):
        processed_files = self.get_user_config_value("processed_files")
        if processed_files is None:
            processed_files = []
            self.set_user_config_value("processed_files", processed_files)
        return processed_files

    def check_for_new_files(self):
        files = os.listdir(self.working_dir)
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

    def import_file(self, filename):
        print(f"Importing: {filename}")

    def detect_delimiter(self, lines):
        counts = {d: sum(line.count(d) for line in lines) for d in SYS_DELIMITERS}
        best = max(counts, key=counts.get)
        # If we found zero delimiters for every candidate, don't guess incorrectly
        if counts[best] == 0:
            raise ValueError(f"Could not detect delimiter from sample. Counts={counts}")
        return best
