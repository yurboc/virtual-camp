import os
import yaml


class Config:
    def __init__(self, env="development"):
        self.conf_file = "config.yaml"
        self.config = self.load_config(env)

    def load_config(self, env):
        with open(os.path.join(os.path.dirname(__file__), self.conf_file), "r") as file:
            config_data = yaml.safe_load(file)
            return config_data.get(env, {})


config = Config(os.getenv("APP_ENV", "development")).config
