from unittest import TestCase
import pandas as pd

from src.season import Season


class TestSeason(TestCase):

    def test_find_team_pseudonyms_shorter_name(self):
        season = Season("test_season", pd.DataFrame(columns=["Team"]), None)
        team_pseudonyms = {
            "Drink Team": ["Drink Team"]
        }
        team_strs = ["Drink"]
        result = season._find_team_pseudonyms(team_pseudonyms, team_strs)
        expected = {
            "Drink Team": ["Drink Team", "Drink"]
        }
        self.assertDictEqual(expected, result)

    def test_find_team_pseudonyms_longer_name(self):
        season = Season("test_season", pd.DataFrame(columns=["Team"]), None)
        team_pseudonyms = {
            "Drink": ["Drink"]
        }
        team_strs = ["Drink Team"]
        result = season._find_team_pseudonyms(team_pseudonyms, team_strs)
        expected = {
            "Drink": ["Drink", "Drink Team"]
        }
        self.assertDictEqual(expected, result)

    def test_find_team_pseudonyms_common_hanoi(self):
        season = Season("test_season", pd.DataFrame(columns=["Team"]), None)
        team_pseudonyms = {
            "Hanoi Drink Team": ["Hanoi Drink Team"],
            "Hanoi Capitals": ["Hanoi Capitals"]
        }
        team_strs = ["Drink Team", "Capitals", "Hanoi Capitals", "Hanoi Drink Team"]
        result = season._find_team_pseudonyms(team_pseudonyms, team_strs)
        expected = {
            "Hanoi Drink Team": ["Hanoi Drink Team", "Drink Team"],
            "Hanoi Capitals": ["Hanoi Capitals", "Capitals"]
        }
        self.assertDictEqual(expected, result)

    def test_find_team_pseudonyms_has_colon(self):
        season = Season("test_season", pd.DataFrame(columns=["Team"]), None)
        team_pseudonyms = {
            "Brothers": ["Brothers"]
        }
        team_strs = ["Brothers", "Brother:"]
        result = season._find_team_pseudonyms(team_pseudonyms, team_strs)
        expected = {
            "Brothers": ["Brothers", "Brother:"]
        }
        self.assertDictEqual(expected, result)

    def test_find_team_pseudonyms_has_hyphen(self):
        season = Season("test_season", pd.DataFrame(columns=["Team"]), None)
        team_pseudonyms = {
            "X-men": ["X-men"]
        }
        team_strs = ["X-men", "X-Men", "X Men"]
        result = season._find_team_pseudonyms(team_pseudonyms, team_strs)
        expected = {
            "X-men": ["X-men", "X-Men", "X Men"]
        }
        self.assertDictEqual(expected, result)

    def test_find_team_pseudonyms_with_viet_letters(self):
        season = Season("test_season", pd.DataFrame(columns=["Team"]), None)
        team_pseudonyms = {
            "FC Thong Nhat": ["FC Thong Nhat"]
        }
        team_strs = ["FC Thong Nhat", 'FC Thông Nhât']
        result = season._find_team_pseudonyms(team_pseudonyms, team_strs)
        expected = {
            "FC Thong Nhat": ["FC Thong Nhat", 'FC Thông Nhât']
        }
        self.assertDictEqual(expected, result)

    def test_find_team_pseudonyms_with_opposite_order(self):
        season = Season("test_season", pd.DataFrame(columns=["Team"]), None)
        team_pseudonyms = {
            "Brothers FC": ["Brothers FC"]
        }
        team_strs = ["Brothers FC", 'FC Brothers']
        result = season._find_team_pseudonyms(team_pseudonyms, team_strs)
        expected = {
            "Brothers FC": ["Brothers FC", 'FC Brothers']
        }
        self.assertDictEqual(expected, result)
