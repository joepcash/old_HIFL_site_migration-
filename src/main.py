import logging
import logging.config
import os
import json
import argparse

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


def get_all_pages(blog_url: str) -> None:
    logger.info(f"Getting all pages from {blog_url}")
    blog = Blog(blog_url)
    blog.save_all_pages()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', type=str, dest='operation', help="The operation you want to run",
                        choices=[
                            "get_all_pages",
                            "get_all_players",
                            "get_all_games"
                        ])
    parser.add_argument("-b", type=str, default="http://hanoiinternationalfootballleague.blogspot.com/",
                        dest="blog_url", help="URL of the blog to operate on")
    args = parser.parse_args()

    configure_logging('logging_config.json')

    if args.operation == 'get_all_pages':
        get_all_pages(args.blog_url)

    # blog = Blog("http://hanoiinternationalfootballleague.blogspot.com/")
    # pages = [Page(url) for url in blog.get_all_page_urls()]
    # page1 = Page("http://hanoiinternationalfootballleague.blogspot.com/")
    # page2 = Page("http://hanoiinternationalfootballleague.blogspot.com/search?updated-max=2016-03-21T17:19:00%2B07:00&max-results=20&start=2&by-date=false")
    # pages = [Page("http://hanoiinternationalfootballleague.blogspot.com/")]

    # for page in pages:
    #     page.get_blog_posts()
