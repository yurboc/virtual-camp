import os
import yaml

MAIN_CONFIG = os.path.join("config", "config.yaml")
TABLES_CONFIG = os.path.join("config", "tables.yaml")
PICTURES_CONFIG = os.path.join("config", "pictures.yaml")


class Config:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        with open(self.config_file, "r", encoding="utf-8") as file:
            config_data = yaml.safe_load(file)
            return config_data


config = Config(config_file=MAIN_CONFIG).config
tables = Config(config_file=TABLES_CONFIG).config
pictures = Config(config_file=PICTURES_CONFIG).config
