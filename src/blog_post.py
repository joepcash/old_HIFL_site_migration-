import logging
from datetime import datetime as dt
import re
from word2number import w2n
import pandas as pd

logger = logging.getLogger(__name__)


class BlogPost:

    def __init__(self, date_outer_div):
        self.date = self._get_date(date_outer_div)
        self.title = self._get_title(date_outer_div)
        self.week = self._get_week(self.title, date_outer_div)
        self.table = self._get_table(date_outer_div)
        self.teams = self._get_teams(self.table)
        self._get_games(date_outer_div)

    @staticmethod
    def _get_date(date_outer_div):
        return dt.strptime(list(list(date_outer_div.find_all("h2",
                                                             class_="date-header")[0].children)[0].children)[0],
                           '%A, %B %d, %Y')

    @staticmethod
    def _get_title(date_outer_div):
        return date_outer_div.find_all("div", class_="MsoNormal")[0].text.strip("\n").strip("\t")

    @staticmethod
    def _get_week(title, date_outer_div):
        for search_text in [title, date_outer_div]:
            week_string = re.findall("Week \\b[A-Za-z]+\\b", str(search_text))[0]
            if week_string:
                return w2n.word_to_num(week_string.split()[1])
        return None

    @staticmethod
    def _get_table(date_outer_div):
        html_table = date_outer_div.find("table")
        if html_table is None:
            return None
        else:
            table = pd.read_html(str(html_table))[0]
            table = table.dropna(axis=1, how='all')
            if table.duplicated().any():
                table.drop_duplicates(inplace=True)
                table.columns = table.iloc[0]
                table = table.drop(table.index[0])

            return table

    @staticmethod
    def _get_teams(table):
        teams = table['Team'].to_list()
        for i in range(len(teams)):
            teams[i] = teams[i].replace("  ", " ")

        return teams

