import logging
import pandas as pd

logger = logging.getLogger(__name__)


def compute_missing_games(blog_posts, include_first=False):
    # Order tables by no. of games played (which should mean chronological)
    blog_posts.sort(key=lambda bp: int(bp.table["P"].sum()))
    # If we're including the first then the difference between itself and the previous is just itself
    if include_first:
        blog_posts[0].diff_table = blog_posts[0].table
    # Subtract the previous table from each table
    for i in range(1, len(blog_posts)):
        blog_posts[i].diff_table = blog_posts[i].table.sort_values("Team").set_index("Team").applymap(int).subtract(
            blog_posts[i-1].table.sort_values("Team").set_index("Team").applymap(int)).reset_index()
    if not include_first:
        blog_posts = blog_posts[1:]
    games = []
    saved_row = pd.DataFrame(columns=[])
    for bp in blog_posts:
        # Only keep rows that played a game
        df_l = bp.diff_table.drop(bp.diff_table[bp.diff_table["P"] == 0].index)
        if not saved_row.empty:
            # If there's a saved row from a previous round of games, add it to this round
            df_l = df_l.append(saved_row).reset_index().drop(["level_0", "index"], axis=1, errors="ignore")
        df_r = df_l.copy(deep=True)
        for index, row in df_l.iterrows():
            if df_r.empty:
                # If there's no games left to match then break the loop
                break
            elif row["Team"] not in df_r["Team"].to_list():
                # If this team has already been removed on a previous iteration, i.e., the match has been found then
                # skip on
                continue
            # Find team in right df that matches the result of this row in left df
            match = df_r[(df_r["F"] == row["A"]) & (df_r["A"] == row["F"]) & (df_r["Team"] != row["Team"])]
            # If a match can't be found save the row to be checked in the next round of games
            if match.empty and int(row["P"]) != 0:
                saved_row = row
                continue
            elif match.empty:
                continue
            match = match.iloc[0]
            # Remove both the matching row and the checked row... I think
            df_r = df_r[~(df_r.eq(match).all(axis=1) | df_r.eq(row).all(axis=1))]
            games.append({"home_team": row["Team"], "away_team": match["Team"], "home_score": row["F"],
                          "away_score": row["A"], "filepath": bp.filepath, "post_title": bp.title, "date": bp.date,
                          "season": bp.season, "competition": "league"})
    games = pd.DataFrame(games)
    return games
