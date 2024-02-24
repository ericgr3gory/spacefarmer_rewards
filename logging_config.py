import logging
from rich.logging import RichHandler
from rich.console import Console
from dotenv import load_dotenv
import os




def setup_log():
    load_dotenv()

    TEMP_DIR = os.environ.get("TEMP_DIR")
    logging.basicConfig(
    filename=f"{TEMP_DIR}/space.log",
    encoding="utf-8",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
    
def setup_rich_logging():
    load_dotenv()

    TEMP_DIR = os.environ.get("TEMP_DIR")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler(f'{TEMP_DIR}/space.log', mode='a', encoding='utf-8')]
    )

    # Create and add the RichHandler for console output
    rich_handler = RichHandler(rich_tracebacks=True)
    #rich_handler.setFormatter(logging.Formatter('%(message)s'))  # Simplified format for console
    logging.getLogger().addHandler(rich_handler)

    
