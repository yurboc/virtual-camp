import os
import yaml

MAIN_CONFIG = os.path.join("config", "config.yaml")
TABLES_CONFIG = os.path.join("config", "tables.yaml")
PICTURES_CONFIG = os.path.join("config", "pictures.yaml")


class Config:
    def __init__(self, config_file, env=None):
        self.config_file = config_file
        self.config = self.load_config(env)

    def load_config(self, env):
        with open(self.config_file, "r") as file:
            config_data = yaml.safe_load(file)
            return config_data.get(env, {}) if env else config_data


config = Config(config_file=MAIN_CONFIG, env=os.getenv("APP_ENV", "development")).config
tables = Config(config_file=TABLES_CONFIG).config
pictures = Config(config_file=PICTURES_CONFIG).config
