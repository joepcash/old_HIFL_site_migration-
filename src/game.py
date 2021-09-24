import logging
import re

from team import Team

logger = logging.getLogger(__name__)


class Game:

    def __init__(self, home_team, home_score, away_score, away_team, goals_str):
        self.home_team = self._get_team(home_team)
        self.home_score = home_score
        self.away_score = away_score
        self.away_team = self._get_team(away_team)
        self.scorers = self._get_all_scorers(goals_str)

    @staticmethod
    def _get_team(team_name):
        return Team(team_name)

    def _get_all_scorers(self, goals_str):
        if not goals_str or ('Goals' not in goals_str and 'goals' not in goals_str):
            return None
        else:
            home_team = None
            away_team = None
            # Search for all variations of each team name in goals_str
            for name in self.home_team.all_names:
                if name in goals_str:
                    home_team = name
                    break
            for name in self.away_team.all_names:
                if name in goals_str:
                    away_team = name
                    break

            home_scorers = []
            away_scorers = []
            unknown_scorers = []
            if home_team:
                home_scorers = self._get_scorers(goals_str, home_team, away_team)
            else:
                logger.warning("Home team name not found in goal scorers string.")
            if away_team:
                away_scorers = self._get_scorers(goals_str, away_team, home_team)
            else:
                logger.warning("Away team name not found in goal scorers string.")
            if not home_team and not away_team:
                unknown_scorers = self._get_scorers(goals_str, None, None)

            return home_scorers + away_scorers + unknown_scorers

    @staticmethod
    def _get_scorers(goals_str, team_name, opponent_team_name):
        # Remove all special characters except commas/dots, isolate list of scorers by team, and split into list using
        # commas
        scorers = re.sub(r'[^.,a-zA-Z0-9 \n\.]', "", goals_str.split(team_name, 1)[1].
                         split(opponent_team_name, 1)[0]).split(",")
        for i in range(len(scorers)):
            # If the scorer string has no letters, then set it to None and skip to next scorer
            if not re.search('[a-zA-Z]', scorers[i]):
                scorers[i] = None
                continue
            # Strip starting/trailing characters/spaces
            scorers[i] = scorers[i].strip(":,.; ")
            # Check if the player has scored multiple goals using the format "playername x <no. of goals>"
            multiple_goals = re.findall(r"(.*)x *([\d]+)", scorers[i])
            if multiple_goals:
                # Strip starting/trailing characters/spaces
                player = multiple_goals[0][0].strip(":,.; ")
                goals = int(multiple_goals[0][-1].strip(":,.; "))
            else:
                # Strip starting/trailing characters/spaces
                player = scorers[i].strip(":,.; ")
                goals = 1
            scorers[i] = {"player": player,
                          "goals": goals,
                          "team": team_name}
        return [s for s in scorers if s is not None]
