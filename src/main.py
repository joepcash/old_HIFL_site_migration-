import logging
import logging.config
import os
import json

from blog import Blog
from page import Page

logger = logging.getLogger(__name__)


def configure_logging(logging_config_path: str) -> None:
    if not os.path.exists(logging_config_path):
        logger.warning(
            f"The logging config file {logging_config_path} could not be "
            f"found. Using default logging configuration")
        return
    with open(logging_config_path) as logging_config_file:
        logging_config = json.load(logging_config_file)
    logging.config.dictConfig(logging_config)
    logger.info("Logging configuration set")

if __name__ == "__main__":
    configure_logging('logging_config.json')
    blog = Blog("http://hanoiinternationalfootballleague.blogspot.com/")
    page_urls = blog.get_all_page_urls()
