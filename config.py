from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    VERSION = "4.1.4"
    BOT_NAME = "Homura"
    CREATOR = "Kanade"
    PREFIX = "$"

config = Config()