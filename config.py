from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    VERSION = "4.2.0"
    BOT_NAME = "Homura"
    CREATOR = "Kanade"
    PREFIX = "$"

config = Config()