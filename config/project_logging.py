import logging
import sys
from datetime import datetime
import warnings
from pathlib import Path

def setup_logger(log_base_name: str = None):
    PROJECT_ROOT = Path("/work/gg0304/g260230/projects/ACE2-Validation")
    sys.path.insert(0, str(PROJECT_ROOT))


    # Suppress warnings for cleaner output
    warnings.filterwarnings('ignore', category=FutureWarning)
    warnings.filterwarnings('ignore', category=RuntimeWarning)

    # Configure logging
    LOG_DIR = PROJECT_ROOT / "logs"
    LOG_DIR.mkdir(exist_ok=True)
    if log_base_name is None:
        LOG_FILE = LOG_DIR / f"tmp-logging-{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    else:
        LOG_FILE = LOG_DIR / f"{log_base_name}-{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger(__name__)

    return logger