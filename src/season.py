import logging
import pandas as pd
from fuzzywuzzy import fuzz
import unicodedata
import csv
import os
import yaml
import numpy as np

logger = logging.getLogger(__name__)


class Season:

    def __init__(self, season_name, final_table, games):
        self.season_name = season_name
        self.final_table = final_table
        # Some weird non-breaking space character has to be replaced with a normal space
        self.teams = [t.replace(u'\xa0', u' ').replace("  ", " ") for t in self.final_table['Team'].to_list()]
        self.games = games
        self.dropouts = self._get_dropouts()
        self.forced_pseudonyms = self._get_forced_pseudonyms()

    def drop_dropouts(self):
        self.games = self.games.loc[(self.games["home_team"].isin(self.teams)) &
                                    (self.games["away_team"].isin(self.teams))]

    def fix_team_name_variation(self):
        team_strs = pd.unique(self.games[['home_team', 'away_team']].values.ravel('K'))
        team_strs = [s for s in team_strs if s not in [p for k, v in self.forced_pseudonyms.items() for p in v]]
        team_pseudonyms = {t: [t] for t in self.teams}
        for k, v in self.forced_pseudonyms.items():
            team_pseudonyms[k].append(v)
        team_pseudonyms = self._find_team_pseudonyms(team_pseudonyms, team_strs)

        def replace_multiple_substrings(row, targets, replacement):
            result = row
            for t in targets:
                result = result.replace(t, replacement)
            return result

        for k, v in team_pseudonyms.items():
            self.games[['home_team', 'away_team']] = \
                self.games[['home_team', 'away_team']].apply(lambda x: replace_multiple_substrings(x, v, k))

    def _find_team_pseudonyms(self, team_pseudonyms, team_strs):
        for k, v in team_pseudonyms.items():
            for ts in team_strs:
                if fuzz.partial_ratio(self._prep_for_fuzz(k), self._prep_for_fuzz(ts)) >= 80 \
                        and ts not in v:
                    team_pseudonyms[k].append(ts)

        unassigned_strs = [ts for ts in team_strs if ts not in [tn for k, v in team_pseudonyms.items() for tn in v]]
        if [str for str in unassigned_strs if str not in self.dropouts]:
            raise RuntimeError(f"The following team strings have not been assigned: {unassigned_strs}")
        return team_pseudonyms

    @staticmethod
    def _prep_for_fuzz(s):
        return ''.join(c for c in unicodedata.normalize('NFD',
                                                        s.lower().replace(":", "").replace("-", "").replace(" ", ""))
                       if unicodedata.category(c) != 'Mn')

    def _get_dropouts(self):
        path = os.path.join("data/dropouts", self.season_name.replace('/', '_') + '.csv')
        if not os.path.isfile(path):
            return []
        dropouts = []
        with open(path, newline='') as inputfile:
            for row in csv.reader(inputfile):
                dropouts.append(row[0])
        return dropouts

    def _get_forced_pseudonyms(self):
        path = os.path.join("data/pseudonyms", self.season_name.replace('/', '_') + '.yml')
        if not os.path.isfile(path):
            return {}
        with open(path) as inputfile:
            pseudoynms = yaml.load(inputfile, Loader=yaml.SafeLoader)
        return pseudoynms

    def remove_void_games(self):
        void_games = pd.read_csv("data/games/void_games.csv")
        self.games = pd.merge(self.games, void_games, how="outer", indicator=True)
        self.games = self.games[self.games._merge == "left_only"].drop(["_merge"], axis=1)

    def fix_duplicate_missing_games(self):
        # Make a full home/away fixture list, i.e., all games that should have been played
        expected_games = pd.DataFrame(columns=["home_team", "away_team"])
        for i in range(len(self.teams)):
            for j in range(i + 1, len(self.teams)):
                expected_games = expected_games.append({"home_team": self.teams[i], "away_team": self.teams[j]},
                                                       ignore_index=True)
                expected_games = expected_games.append({"home_team": self.teams[j], "away_team": self.teams[i]},
                                                       ignore_index=True)
        # Compare actual game list with expected to identify missing games
        missing_games = pd.concat([self.games.copy(), expected_games]).drop_duplicates(
            ["home_team", "away_team"], keep=False)
        # Find fixtures that were supposedly played twice
        duplicate_games = self.games[self.games.duplicated(["home_team", "away_team"], False)]
        # Swap home/away teams for all duplicate fixtures
        duplicates_flipped = duplicate_games.rename(columns={"home_team": "away_team", "away_team": "home_team",
                                                             "home_score": "away_score", "away_score": "home_score"})
        duplicates_flipped = pd.DataFrame({"home_team": duplicate_games["away_team"],
                                           "away_team": duplicate_games["home_team"],
                                           "home_score": duplicate_games["away_score"],
                                           "away_score": duplicate_games["home_score"],
                                           "filepath": duplicate_games["filepath"],
                                           "post_title": duplicate_games["post_title"],
                                           "date": duplicate_games["date"],
                                           "season": duplicate_games["season"],
                                           "competition": duplicate_games["competition"]})
        # Check if any of the duplicate games were actually written with wrong home/away order by checking if their
        # flipped versions can be found in the missing games list
        flipped_games = duplicates_flipped.merge(missing_games[["home_team", "away_team"]],
                                                 on=["home_team", "away_team"]).sort_values(
            "date").drop_duplicates(["home_team", "away_team"], keep="last")
        # For any games in which this is true, add them to the games list with the more recent fixture flipped home/away
        self.games = self.games.append(flipped_games)
        # Find the flipped games in the original (incorrect) home/away order and remove them from the games list while
        # keeping the previously added flipped versions
        flipped_games_original = flipped_games.rename(columns={"home_team": "away_team", "away_team": "home_team",
                                                               "home_score": "away_score", "away_score": "home_score"})
        self.games = pd.merge(self.games,
                              flipped_games_original[["home_team", "away_team", "home_score", "away_score"]],
                              on=["home_team", "away_team", "home_score", "away_score"], indicator=True,
                              how='outer').query('_merge=="left_only"').drop('_merge', axis=1)
        # Any remaining duplicates are legitimate duplicates, for each one keep the most recent game (as sometimes)
        # a game has been written off as a walkover and then later actually played
        self.games = self.games.sort_values("date").drop_duplicates(["home_team", "away_team"], keep="last")
        missing_games = pd.concat([self.games.copy(), expected_games]).drop_duplicates(
            ["home_team", "away_team"], keep=False)
        if not missing_games.empty:
            missing_games_str = ", ".join([r[0] + " vs. " + r[1] for r in
                                           missing_games[["home_team", "away_team"]].values])
            logger.warning(f"The following games are missing: {missing_games_str}")

    def play_season(self):
        table = self.final_table.copy()
        table[table.columns.difference(["Rank", "Team"])] = 0

        self.games["home_win"] = self.games["away_win"] = self.games["Draw"] = 0
        self.games.loc[:, "home_win"][(self.games["home_score"] - self.games["away_score"]) > 0] = 1
        self.games.loc[:, "away_win"][(self.games["home_score"] - self.games["away_score"]) < 0] = 1
        self.games.loc[:, "Draw"][(self.games["home_score"] - self.games["away_score"]) == 0] = 1

        home_table = self.games.loc[:, ["home_team", "home_win", "Draw", "away_win", "home_score", "away_score"]] \
            .rename(columns={"home_team": "Team", "home_win": "Won", "away_win": "Loss",
                             "home_score": "GF", "away_score": "GA"}).groupby("Team").sum()
        home_table["Points"] = 3 * home_table["Won"] + home_table["Draw"]
        home_table["Played"] = home_table["Won"] + home_table["Draw"] + home_table["Loss"]
        home_table["Goal difference"] = home_table["GF"] - home_table["GA"]
        away_table = self.games.loc[:, ["away_team", "away_win", "Draw", "home_win", "away_score", "home_score"]] \
            .rename(columns={"away_team": "Team", "away_win": "Won", "home_win": "Loss",
                             "away_score": "GF", "home_score": "GA"}).groupby("Team").sum()
        away_table["Points"] = 3 * away_table["Won"] + away_table["Draw"]
        away_table["Played"] = away_table["Won"] + away_table["Draw"] + away_table["Loss"]
        away_table["Goal difference"] = away_table["GF"] - away_table["GA"]
        complete_table = home_table.add(away_table, fill_value=0)
        complete_table = complete_table.reset_index().rename(columns={"Won": "W", "Draw": "D", "Loss": "L",
                                                                      "GF": "F", "GA": "A", "Points": "Pts",
                                                                      "Played": "P", "Goal difference": "GD"})
        # diff_table = self.final_table.sort_values("Team").set_index("Team").applymap(int)\
        #     .subtract(complete_table.sort_values("Team").set_index("Team").applymap(int), axis=1).reset_index()
        # finalised_games = pd.DataFrame(columns=["Date dd/mm/yyyy", "Time HH:MM", "Division", "Home Team", "Away Team",
        #                                         "Venue", "Pitch", "Home Score", "Away Score"])
        finalised_games = self.games.rename(columns={"home_team": "Home Team", "away_team": "Away Team",
                                                     "home_score": "Home Score", "away_score": "Away Score",
                                                     "date": "Date dd/mm/yyyy"})
        finalised_games = finalised_games.reindex(columns=["Date dd/mm/yyyy", "Time HH:MM", "Division", "Home Team",
                                                           "Away Team", "Venue", "Pitch", "Home Score", "Away Score"])
        finalised_games["Time HH:MM"] = "14:00"
        finalised_games["Division"] = "HIFL League"
        finalised_games["Date dd/mm/yyyy"] = pd.to_datetime(finalised_games["Date dd/mm/yyyy"]).dt.strftime("%d/%m/%Y")
        finalised_games["Home Score"] = pd.to_numeric(finalised_games["Home Score"], downcast="integer")
        finalised_games["Away Score"] = pd.to_numeric(finalised_games["Away Score"], downcast="integer")
        finalised_games["Home Team"] = self.use_site_names(finalised_games["Home Team"])
        finalised_games["Away Team"] = self.use_site_names(finalised_games["Away Team"])
        finalised_games[["Date dd/mm/yyyy", "Time HH:MM", "Division", "Home Team", "Away Team", "Venue", "Pitch",
                        "Home Score", "Away Score"]].to_csv(
            f"data/finalised_games/{self.season_name.replace('/','-')}.csv", index=False)

    def use_site_names(self, team_col):
        with open("data/match_site_names/match_site_names.yml") as inputfile:
            site_names = yaml.load(inputfile, Loader=yaml.SafeLoader)

        return team_col.replace(site_names)


    def find_missing_games(self):
        expected_games = pd.DataFrame(columns=["home_team", "away_team"])
        for i in range(len(self.teams)):
            for j in range(i + 1, len(self.teams)):
                expected_games = expected_games.append({"home_team": self.teams[i], "away_team": self.teams[j]},
                                                       ignore_index=True)
                expected_games = expected_games.append({"home_team": self.teams[j], "away_team": self.teams[i]},
                                                       ignore_index=True)

        missing_games = pd.concat([self.games[["home_team", "away_team"]].copy(), expected_games]).drop_duplicates(
            keep=False)
        print("Done")
