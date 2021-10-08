import logging
import re
from fuzzywuzzy import process, fuzz

from src.team import Team

logger = logging.getLogger(__name__)


class Game:

    def __init__(self):
        self.url = None
        self.filepath = None
        self.date = None
        self.season = None
        self.game_str = None
        self.home_team = None
        self.home_score = None
        self.away_team = None
        self.away_score = None
        self.goals_str = None
        self.scorers = None

    def prepare(self, url, filepath, date, season, game_str, home_team, home_score, away_score, away_team, goals_str=None):
        self.url = url
        self.filepath = filepath
        self.date = date
        self.season = season
        self.game_str = game_str
        self.home_team = self._get_team_name(home_team)
        self.home_score = int(home_score)
        self.away_score = int(away_score)
        self.away_team = self._get_team_name(away_team)
        self.goals_str = goals_str

        return self

    @staticmethod
    def _get_team(team_name):
        return Team(team_name)

    @staticmethod
    def _get_team_name(team_name_str):
        # Find team name in string
        team_name = re.findall(r"([^()]*)( (\((.*)\)))?", team_name_str)[0][0]
        # Strip characters from each end of team name
        team_name = team_name.strip(" #_*")
        # Remove numbering from list at start of string. e.g., "4. Team Name"
        team_name = re.sub(r"\d. ", "", team_name)

        return team_name

    def get_all_scorers(self):
        if self.goals_str is None:
            return
        regex_patterns = [f"Goals: ({self.home_team}):?([^;]*);? ?(?:({self.away_team}):?(.*))",
                          r"Goals: (.*):(.*);( (.*):(.*).)?",
                          r"Goals: (.*):(.*)\.(.*)(.*)(.*)",
                          r"Goals: (.*):(.*)(.*)(.*)(.*)",
                          f"Goals: ({self.home_team})(.*)(({self.away_team})(.*))"]
        for reg in regex_patterns:
            found = re.findall(reg, self.goals_str)
            if found:
                goal_str_els = [x.strip(" ,;") for x in list(found[0])]
                break
        team_scorers_strs = []
        scorers = []
        if goal_str_els[0]:
            team_scorers_strs.append(tuple(goal_str_els[0:2]))
        if goal_str_els[-2]:
            team_scorers_strs.append(tuple(goal_str_els[-2:]))
        for tss in team_scorers_strs:
            team = process.extractOne(tss[0], [self.home_team, self.away_team])
            if team[-1] > 90:
                team = team[0]
            else:
                continue
            scorers.extend(self._get_scorers_for_team(tss[1], team))

        if self.home_score != sum([s["goals"] for s in scorers if s["team"] == self.home_team]) and \
                goal_str_els[1] not in ["?"]:
            logger.warning("There are unaccounted for home team goals")
        if self.away_score != sum([s["goals"] for s in scorers if s["team"] == self.away_team]) and \
                goal_str_els[-1] not in ["?"]:
            logger.warning("There are unaccounted for away team goals")

        self.scorers = scorers

    @staticmethod
    def _get_scorers_for_team(scorers_str, team):
        scorers = [{"name": s.strip(), "team": team} for s in re.split(',(?![^\(\[]*[\]\)])', scorers_str)]
        # If the scorer string isn't a name, then remove it
        scorers = [s for s in scorers if s["name"] not in ["?"]]
        # Count goals
        for i in range(len(scorers)):
            # Check for multiple goals in the format "name x N"
            multiple_goals_x = re.findall(r"(.*)x *([\d]+)", scorers[i]["name"])
            # Check for multiple goals in the format "name (time, time, ...)"
            multiple_goals_bracket = re.findall(r"(.*)\((.*)\)", scorers[i]["name"])
            if multiple_goals_x:
                scorers[i]["name"] = multiple_goals_x[0][0].strip()
                scorers[i]["goals"] = int(multiple_goals_x[0][-1])
            elif multiple_goals_bracket:
                scorers[i]["name"] = multiple_goals_bracket[0][0].strip()
                scorers[i]["goals"] = len(multiple_goals_bracket[0][-1].split(","))
            else:
                scorers[i]["goals"] = 1

        return scorers
