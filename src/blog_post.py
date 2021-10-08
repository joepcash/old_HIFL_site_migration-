import logging
from datetime import datetime as dt
import re
from word2number import w2n
import pandas as pd
import html2text
import os

from src.game import Game

logger = logging.getLogger(__name__)


class BlogPost:

    def __init__(self, url, filepath, post_html, date, season):
        self.url = url
        self.filepath = filepath
        self.post_html = post_html
        self.date = date
        self.season = season
        self.title = None
        self.is_unneeded_post = False
        self.week = None
        self.table = None
        self.teams = None
        self.games = None

    def prepare(self, get_scorers=True):
        self.get_title()
        if self.is_unneeded_post:
            return self
        self.get_week()
        self.get_table()
        self.get_teams()
        self.get_games(get_scorers)

        return self

    def get_title(self):
        html_text = html2text.html2text(str(self.post_html))
        # Find all hyperlinks
        hyperlinks = self.find_hyperlinks_in_text(html_text)
        # Clean hyperlink text
        hl_text_clean = ["\n" * h[0].startswith("\n") + h[0].replace("\n", " ") + "\n" * h[0].endswith("\n") for h in
                         hyperlinks]
        # Replace all hyperlinks with just their text
        for replace, original in zip(hl_text_clean, hyperlinks):
            html_text = html_text.replace("".join(["[", original[0], "](", original[1], ")"]), replace)
        # Remove bold markers and pound signs
        html_text = html_text.replace("**", "").replace("#", "")
        # Remove empty lines
        html_text = os.linesep.join([s for s in html_text.splitlines() if s and not s.isspace()])
        # Return the first line which contains alphabet characters
        for line in html_text.splitlines():
            if re.search('[a-zA-Z]', line):
                self.title = line.strip("\n ").strip("\t")
                self.check_is_unneeded_post()
                return

    def check_is_unneeded_post(self):
        unneeded_titles = ["Welcome to HIFL 2012/13", "HIFL 2012-13 Cup Draw", "League Schedule 2012/13",
                           "League 2010-2011 -- Fixtures", "Disciplinary Panel", "Updated Schedule 2012/13",
                           "HIFL Draft Rules", "Join the Hanoi International Football League now!",
                           "The 2011-2012 League has finally ended with a double title for Drink Team.",
                           "HIFL 2011-2012 at a glance", "2011-2012 League Fixture", "FC Thống Nhất Champion!",
                           "Week One - We're Off!", "The weekend Fixtures", "So it begins.....",
                           "Some pictures from the 7 a side tournament bia hoi session", "Pre Season 7-a-side fun.",
                           "2013-2014 Season", "Remaining Fixtures", "Cup Scorers", "HIFL Fixtures 16/3",
                           "HIFL Cup Draw", "Super Cup - October 15", "Pitches venue", "Captains meeting",
                           "Roots Bar Tournament - Results", "7th Roots Bar Trounament - June 18th",
                           "HIFL 2010-2011 at a glance", "Day 14 (last day) -- 14-15/05",
                           "Chúc mừng năm mới xuân Tân Mão 2011!", "Catch Up Calendar"]
        if self.title in unneeded_titles:
            self.is_unneeded_post = True
        else:
            self.is_unneeded_post = False

    @staticmethod
    def find_hyperlinks_in_text(html_text):
        html_text = html_text.strip(" \n[]")
        return re.findall(r"\[((?:[^\[]|\n?)*?)(?:\])\(((?:.|\n)*?)\)", html_text)

    def get_week(self):
        week_strings = re.findall("Week \\b[A-Za-z]+\\b", self.title)
        if week_strings:
            self.week = w2n.word_to_num(week_strings[0].split()[1])

    def get_table(self):
        html_table = self.post_html.find("table")
        if html_table is None:
            return
        else:
            table = pd.read_html(str(html_table))[-1]
            table = table.dropna(axis=1, how='all')
            if table.duplicated().any():
                table.drop_duplicates(inplace=True)
                table.columns = table.iloc[0]
                self.table = table.drop(table.index[0])

            return table

    def get_teams(self):
        if self.table is None:
            return
        teams = self.table['Team'].to_list()
        for i in range(len(teams)):
            teams[i] = teams[i].replace("  ", " ")

        self.teams = teams

    def get_games(self, get_scorers=True):
        # Convert html to text
        html_text = html2text.html2text(str(self.post_html))
        # Remove bold markers
        html_text = html_text.replace("**", "")
        # Remove empty lines
        html_text = os.linesep.join([s for s in html_text.splitlines() if s and not s.isspace()])

        # Find games and split into parts using regex
        games = self.find_games_in_text(html_text)
        games = [list(g) for g in games]
        # Remove strings that were accidentally captured as games
        filtered_games = []
        for game in games:
            if not any(s in game[0] for s in ["Match Day"]):
                filtered_games.append(game)
        games = filtered_games
        if get_scorers:
            games = self._get_scorers_str(games, html_text)
        # games = re.findall(r"(.*) ([\d]{1,2}) [–-] ([\d]{1,2}) (.*)([\r\n]+[^\r\n]+)?", html_text)
        # Save games as game object
        games = [Game().prepare(self.url, self.filepath, self.date, self.season, *g) for g in games]
        if get_scorers:
            games = [g.get_all_scorers() for g in games]

        self.games = games

    @staticmethod
    def find_games_in_text(html_text):
        return re.findall(r"((.*) ([\d]{1,2}) ?[–-] ?([\d]{1,2}) (.*?)(?: \(|\n|$)(?:(.*)\))?)", html_text)

    @staticmethod
    def _get_scorers_str(games, html_text):
        lines = html_text.splitlines()
        # Find all games in html text and append goals string to game's list
        for i in range(len(lines)):
            for j in range(len(games)):
                if lines[i] == games[j][0]:
                    if lines[i + 1].startswith("Goals: "):
                        if lines[i + 1].endswith((";", ",")):
                            games[j].append(lines[i + 1] + " " + lines[i + 2])
                        else:
                            games[j].append(lines[i + 1])

        # Any games for which a goal string wasn't found, add a none goal string
        for j in range(len(games)):
            if len(games[j]) == 4:
                games[j].append(None)

        return games
