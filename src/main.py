import logging
import logging.config
import os
import json
import argparse

import pandas as pd

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


def get_all_pages(blog: Blog) -> None:
    logger.info(f"Getting all pages from {blog.url}")
    blog.save_all_pages()


def get_all_games() -> None:
    logger.info("Getting all games")
    page_dir = "data/pages"
    blog_posts = []
    games = []
    for file in os.listdir(page_dir):
        filename = os.fsdecode(file)
        filepath = os.path.join(page_dir, filename)
        page = Page(None, filepath)
        page.get_blog_posts("local")
        for bp in page.blog_posts:
            blog_posts.append(bp)
            for g in bp.games:
                game = {
                    "home_team": g.home_team,
                    "away_team": g.away_team,
                    "home_score": g.home_score,
                    "away_score": g.away_score,
                    "filepath": g.filepath,
                    "post_title": bp.title,
                    "date": g.date,
                    "season": g.season
                }
                games.append(game)
        games_df = pd.DataFrame(games)
        games_df.to_csv("data/games/games.csv", index=False)
        logger.info(f"{filename} complete")


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
    blog = Blog(args.blog_url)

    if args.operation == 'get_all_pages':
        get_all_pages(blog)
    elif args.operation == "get_all_games":
        get_all_games()
