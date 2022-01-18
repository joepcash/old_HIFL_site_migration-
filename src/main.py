import logging
import logging.config
import os
import json
import argparse
from pathlib import Path

import pandas as pd

from blog import Blog
from page import Page
from season import Season
from compute_missing_games import compute_missing_games

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
        # page = Page(None, "data/pages/page28.html")
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
                    "season": g.season,
                    "competition": g.competition
                }
                games.append(game)
        logger.info(f"{filename} complete")
    games_df = pd.DataFrame(games)
    missing_games_14_15_1 = [bp for bp in blog_posts if bp.title in ["Position", "Week 2 - Two perfect records survive.",
                                                         "Week 3 - Three teams go three games undefeated.",
                                                         "Week 4: Especially four you."]
                  and bp.season == "2014/15"]
    missing_games_14_15_1 = compute_missing_games(missing_games_14_15_1, True)
    games_df = pd.concat([games_df, missing_games_14_15_1])
    missing_games_14_15_2 = [bp for bp in blog_posts if
                             bp.title in ["Week 14 - Crawling to the finish line", "Final Table"]
                             and bp.season == "2014/15"]
    missing_games_14_15_2 = compute_missing_games(missing_games_14_15_2, False)
    games_df = pd.concat([games_df, missing_games_14_15_2])
    games_df.to_csv("data/games/games.csv", index=False)
    logger.info("Got all games")


def get_final_table_all_seasons() -> None:
    logger.info("Getting final tables")
    page_dir = "data/pages"
    blog_posts = []
    tables = []
    for file in os.listdir(page_dir):
        filename = os.fsdecode(file)
        filepath = os.path.join(page_dir, filename)
        page = Page(None, filepath)
        page.get_blog_posts("local")
        for bp in page.blog_posts:
            blog_posts.append(bp)
            if bp.table is not None:
                tables.append({"date": bp.date,
                               "season": bp.season,
                               "table": bp.table})
        logger.info(f"{filename} complete")
    tables_df = pd.DataFrame(tables)
    tables_df = tables_df[tables_df.groupby("season")["date"].transform("max") == tables_df["date"]]
    tables_df = tables_df.drop_duplicates(["date", "season"])
    tables_df.apply(lambda x: x["table"].to_csv(f"data/final_tables/{x['season'].replace('/', '_')}.csv",
                                                index=False), axis=1)
    logger.info("Got all final tables")


def get_cup_participants() -> None:
    logger.info("Getting cup participants")
    page_dir = "data/pages"
    cup_participants = []
    for file in os.listdir(page_dir):
        filename = os.fsdecode(file)
        filepath = os.path.join(page_dir, filename)
        page = Page(None, filepath)
        blog_posts = page.get_cup_posts("local")
        for bp in blog_posts:
            cup_participants.append(bp.get_cup_participants())
        logger.info(f"{filename} complete")
    cup_participants = [c for c in cup_participants if c["teams"]]
    logger.info("Got all cup participants")


def get_games_by_season() -> None:
    games_df = pd.read_csv("data/games/games.csv")
    missing_games_df = pd.read_csv("data/games/missing_games.csv")
    corrected_games_df = pd.read_csv("data/games/corrected_games.csv")
    games_df = pd.concat([games_df, missing_games_df])
    games_df = games_df.set_index(["home_team", "away_team", "season", "competition"])
    corrected_games_df = corrected_games_df.set_index(["home_team", "away_team", "season", "competition"])
    games_df.update(corrected_games_df)
    games_df.reset_index(inplace=True)
    page_dir = "data/final_tables"
    seasons = []
    for file in os.listdir(page_dir):
        filename = os.fsdecode(file)
        filepath = os.path.join(page_dir, filename)
        season_name = Path(filename).stem.replace('_', '/')
        df = pd.read_csv(filepath)
        season_games = games_df[(games_df['season'] == season_name) & (games_df["competition"] == "league")]
        season = Season(season_name, df, season_games)
        season.fix_team_name_variation()
        season.drop_dropouts()
        season.remove_void_games()
        season.fix_duplicate_missing_games()
        season.play_season()
        seasons.append(season)


def find_missing_games() -> None:
    games_df = pd.read_csv("data/games/games.csv")
    page_dir = "data/final_tables"
    seasons = []
    for file in os.listdir(page_dir):
        filename = os.fsdecode(file)
        filepath = os.path.join(page_dir, filename)
        season_name = Path(filename).stem.replace('_', '/')
        df = pd.read_csv(filepath)
        season_games = games_df[(games_df['season'] == season_name) & (games_df["competition"] == "league")]
        season = Season(season_name, df, season_games)
        season.fix_team_name_variation()
        season.find_missing_games()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', type=str, dest='operation', help="The operation you want to run",
                        choices=[
                            "get_all_pages",
                            "get_all_players",
                            "get_all_games",
                            "get_all_final_tables",
                            "play_seasons",
                            "get_cup_participants",
                            "find_missing_games"
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
    elif args.operation == "get_all_final_tables":
        get_final_table_all_seasons()
    elif args.operation == "play_seasons":
        get_games_by_season()
    elif args.operation == "get_cup_participants":
        get_cup_participants()
    elif args.operation == "find_missing_games":
        find_missing_games()