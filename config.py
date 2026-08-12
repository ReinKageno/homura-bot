from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    VERSION = "0.5.4"
    BOT_NAME = "Homura"
    CREATOR = "Kanade"
    PREFIX = "$"
    MASTER = 123456789012345678
    SAWERIA = "https://saweria.co/kanaede"

config = Config()