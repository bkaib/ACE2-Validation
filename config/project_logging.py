import logging
import sys
from datetime import datetime
import warnings
from pathlib import Path
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
from queue import Queue
import threading

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


def setup_parallel_logger(log_base_name: str = None, use_queue_listener: bool = True):
    """
    Setup a thread-safe logger suitable for Dask parallelization.
    
    This logger uses QueueHandler + QueueListener to serialize log messages
    from multiple threads to a single file, preventing race conditions and
    interleaved output.
    
    Args:
        log_base_name: Base name for the log file
        use_queue_listener: If True, use QueueHandler+QueueListener (thread-safe).
                           If False, use basic logging (faster but less safe).
    
    Returns:
        tuple: (logger, queue_listener) where queue_listener is None if not used.
               If using queue_listener, keep it in scope while logging is active.
    """
    PROJECT_ROOT = Path("/work/gg0304/g260230/projects/ACE2-Validation")
    sys.path.insert(0, str(PROJECT_ROOT))

    # Suppress warnings for cleaner output
    warnings.filterwarnings('ignore', category=FutureWarning)
    warnings.filterwarnings('ignore', category=RuntimeWarning)

    LOG_DIR = PROJECT_ROOT / "logs"
    LOG_DIR.mkdir(exist_ok=True)
    
    if log_base_name is None:
        LOG_FILE = LOG_DIR / f"parallel-logging-{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    else:
        LOG_FILE = LOG_DIR / f"{log_base_name}-{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s')
    
    if use_queue_listener:
        # Create a queue for thread-safe logging
        log_queue = Queue()
        
        # Create handlers that will write to the queue
        queue_handler = QueueHandler(log_queue)
        
        # Create actual file and stream handlers that will be managed by QueueListener
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=100*1024*1024, backupCount=5  # 100MB per file, keep 5 backups
        )
        file_handler.setFormatter(formatter)
        
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        
        # Create QueueListener to handle all logging from the queue
        queue_listener = QueueListener(log_queue, file_handler, stream_handler, respect_handler_level=True)
        queue_listener.start()
        
        # Configure root logger to use QueueHandler
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(queue_handler)
        
        logger = logging.getLogger(__name__)
        return logger, queue_listener
    
    else:
        # Fallback to basic logging (Python logging is thread-safe at basic level)
        logging.basicConfig(
            level=logging.INFO,
            format=formatter._fmt,
            handlers=[
                RotatingFileHandler(LOG_FILE, maxBytes=100*1024*1024, backupCount=5),
                logging.StreamHandler(sys.stdout)
            ]
        )
        logger = logging.getLogger(__name__)
        return logger, None