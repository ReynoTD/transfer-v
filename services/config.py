import os
from dotenv import load_dotenv

load_dotenv()

DEBUG = os.getenv("DEBUG", "false").lower() == "true"
DEBUG_PAUSE_SECONDS = int(os.getenv("DEBUG_PAUSE_SECONDS", "0"))
