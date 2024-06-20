import json
import os

from pydantic import BaseModel

if not os.path.exists('data'):
    os.mkdir('data')

config_file = 'data/config.json'


class ServerConfig(BaseModel):
    port: int = 5555


class ModelConfig(BaseModel):
    yolo_path: str = './best.pt'


class BackendServerConfig(BaseModel):
    server: ServerConfig = ServerConfig()
    model: ModelConfig = ModelConfig()

    def __init__(self):
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                super().__init__(**json.load(f))
        else:
            super().__init__()

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.model_dump(), f, ensure_ascii=True, sort_keys=True, indent=4)


config = BackendServerConfig()
