import logging
import os

def setup_logging():
    log_file = "aws_porter.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            # We don't add StreamHandler here because rich console handles output
        ]
    )
    return logging.getLogger("aws_porter")
