from dataclasses import dataclass
import os
import shutil

@dataclass(frozen=True)
class Config:
    VERSION = "0.6.1"
    BOT_NAME = "Homura"
    CREATOR = "Kanade"
    PREFIX = "$"
    FFMPEG_PATH = os.getenv("FFMPEG_PATH") or shutil.which("ffmpeg") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools/ffmpeg/bin", "ffmpeg")
    MASTER = 123456789012345678
    SAWERIA = "https://saweria.co/kanaede"

config = Config()