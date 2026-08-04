from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    VERSION = "4.0.0"
    BOT_NAME = "Homura"
    CREATOR = "Kanade"
    PREFIX = "!"

config = Config()