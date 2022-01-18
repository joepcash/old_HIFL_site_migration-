import unittest

from src.game import Game


class GameTests(unittest.TestCase):

    def test_get_scorers_away_unknown_multi_scorer(self):
        game = Game()
        game.goals_str = "Goals: Minsk: Jo x 2, Frazier, Joey, Adam; Drink: ?"
        game.home_team = "Minsk"
        game.away_team = "Drink"
        game.home_score = 5
        game.away_score = 1
        game.get_all_scorers()
        expected = [{"name": "Jo", "goals": 2, "team": "Minsk"},
                    {"name": "Frazier", "goals": 1, "team": "Minsk"},
                    {"name": "Joey", "goals": 1, "team": "Minsk"},
                    {"name": "Adam", "goals": 1, "team": "Minsk"}]
        self.assertCountEqual(game.scorers, expected)

    def test_get_scorers_no_away_team_period(self):
        game = Game()
        game.goals_str = "Goals: Roots: David x 2, Nico."
        game.home_team = "Roots"
        game.away_team = "Capitals"
        game.home_score = 3
        game.away_score = 0
        game.get_all_scorers()
        expected = [{"name": "David", "goals": 2, "team": "Roots"},
                    {"name": "Nico", "goals": 1, "team": "Roots"}]
        self.assertCountEqual(game.scorers, expected)

    def test_get_scorers_missing_away_colon_mins_inc(self):
        game = Game()
        game.goals_str = "Goals: Capitals: Renato (10 , 30), Roots Mai (80), Osh (85)"
        game.home_team = "Capitals"
        game.away_team = "Roots"
        game.home_score = 2
        game.away_score = 2
        game.get_all_scorers()
        expected = [{"name": "Renato", "goals": 2, "team": "Capitals"},
                    {"name": "Mai", "goals": 1, "team": "Roots"},
                    {"name": "Osh", "goals": 1, "team": "Roots"}]
        self.assertCountEqual(game.scorers, expected)

    def roots_game_with_week_result_page_10_week_13(self):
        pass
        # Make test for Roots game that has "Week Result -" at start of game string on page10.html, Week 13