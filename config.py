from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    VERSION = "4.1.3"
    BOT_NAME = "Homura"
    CREATOR = "Kanade"
    PREFIX = "$"

config = Config()