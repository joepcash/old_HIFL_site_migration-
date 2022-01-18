

class Team:

    def __init__(self, team_name):
        team_name = team_name.strip()
        self.name = team_name
        self.all_names = self._get_all_names(team_name)

    @staticmethod
    def _get_all_names(team_name):
        all_names = [team_name]
        words = team_name.split()
        if len(words) > 1:
            for i in range(1, len(words)):
                all_names.append(" ".join(words[:-1*i]))

        return all_names
