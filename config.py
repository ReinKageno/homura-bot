from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    VERSION = "4.2.4"
    BOT_NAME = "Homura"
    CREATOR = "Kanade"
    PREFIX = "$"
    MASTER = 123456789012345678

config = Config()