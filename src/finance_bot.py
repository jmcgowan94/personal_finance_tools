import json
import os
from pathlib import Path
import questionary
import sys

class FinanceBot:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.user_config = self.get_user_config()
        self.working_dir = self.get_working_dir()

    def get_user_config(self):
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

    def get_working_dir(self):
        if "working_dir" not in self.user_config:
            current_dir = Path.home()
            filepath_set = False
            while not filepath_set:
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
                    f"Current filepath: {current_dir}\n  Continue navigating, or choose 'DONE'",
                    choices=options
                ).ask()
                if user_input == "EXIT":
                    print("Exiting script.\n")
                    sys.exit()
                elif user_input == "DONE":
                    self.set_user_config_value("working_dir", f"{current_dir}")
                    filepath_set = True
                elif user_input == "BACK":
                    current_dir = current_dir.parent
                else:
                    current_dir = current_dir / user_input
        return self.user_config["working_dir"]

    def set_user_config_value(self, key, value):
        self.user_config[key] = value
        user_config_path = self.project_root / "private" / "user_config.json"
        with user_config_path.open(mode="w") as f:
            json.dump(self.user_config, f, indent=2)
