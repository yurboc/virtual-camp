import os
import yaml

CONF_FILE = os.path.join("config", "config.yaml")


class Config:
    def __init__(self, env="development"):
        self.conf_file = CONF_FILE
        self.config = self.load_config(env)

    def load_config(self, env):
        with open(self.conf_file, "r") as file:
            config_data = yaml.safe_load(file)
            return config_data.get(env, {})


config = Config(os.getenv("APP_ENV", "development")).config
