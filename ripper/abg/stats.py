import pandas as pd
import numpy as np
from pprint import pprint as pp
import datetime
import re
import math
import logging
from abg.elo import ELO

l = logging.getLogger("abg")

def read_match_csv(file_handle):
    return pd.read_csv(file_handle, parse_dates=["match-completed-at", "created-at", "completed-at", "match-completed-at", "created-at"], dtype={"match-scores-csv": str})

def clean_matches(abg):
    abg = abg[["name", "match-id", "match-scores-csv", "completed-at", "match-completed-at", "created-at", "player1-name", "player2-name", "DQ", "DQ_text"]]
    abg.set_index("match-id", inplace=True)

    abg["match-completed-at"].fillna(abg["completed-at"],inplace=True)
    abg["match-completed-at"].fillna(abg["created-at"],inplace=True)

    abg.sort_values("match-completed-at", inplace=True)
    del abg["created-at"]

    f = abg["match-scores-csv"].apply(lambda x: pd.Series(str(x).split("-")))
    abg.loc[:,("player1-score")] = f[0]
    #@todo abg["player1-score"].astype(int8)
    abg.loc[:,("player1-score")] = pd.to_numeric(abg["player1-score"], errors='coerce')
    abg.loc[:,("player2-score")] = f[1]
    abg.loc[:,("player2-score")] = pd.to_numeric(abg["player2-score"], errors='coerce')

    abg.loc[:,("match-length")] = abg[["player1-score", "player2-score"]].apply(max, axis=1)

    # @Todo: gives a simple histogram of sorts.
    #abg["match-length"].count_values()
    abg['match-length'].fillna(0,inplace=True)
    abg = abg.drop(abg[abg["match-length"] == 0].index)

    ## @TODO: remove this.
    abg['match-length'].fillna(0,inplace=True)

    def match_length_fix(row):
        if (row["match-length"] == 1):
            row["match-length"] = 7
            if (row["player1-score"] > row["player2-score"]):
                row["player1-score"] = 7
            else:
                row["player2-score"] = 7
        return row

    abg = abg.apply(match_length_fix, axis=1)

    abg["player1_ELO"] = 1500
    abg["player2_ELO"] = 1500
    # abg['winchance'] = .5
    abg["player1_ELO_change"] = 0
    abg["player2_ELO_change"] = 0

    return abg


def build_players(abg):
    #abg["player1-win_chance"] =
    #elo = pd.DataFrame({}, columns=['player1-name', 'player2-name', 'player1-id', 'player2-id'])
    p1 = abg.ix[:,['player1-name']].rename(columns={"player1-name": "player_name"})
    p2 = abg.ix[:,['player2-name']].rename(columns={"player2-name": "player_name"})

    p1.reset_index(inplace=True,drop=True)
    p2.reset_index(inplace=True,drop=True)


    #@TODO: check out pd.concat()
    players = p1.append(p2)
    players.drop_duplicates(inplace=True)
    players = players.reset_index(drop=True)

    players["ELO"] = 1500
    players["xp"] = 0
    players["last_updated"] = None
    players["last_updated"] = pd.to_datetime(players["last_updated"])
    return players

def tournament_type_finder(tournament_name):
    tournament_types = {
        "Goldilocks":["Goldilocks"],
        "Masters":["Masters"],
        "Ironman":["Iron"],
        "Seriously Fun Swiss":["Seriously Fun"],
        "Travis":["t.r.a", "travis"],
        "Stair Step":["Stair"],
        "Champion and Challenger":["Challenger"],
        "Spur of the moment": ["Spur"],
        "Mini": ["Mini"]
    }

    for val,search_strings in tournament_types.items():
        for search_string in search_strings:
            r = re.compile(search_string, re.IGNORECASE)
            if(r.match(tournament_name)):
                return val
    return "general"

def set_tournament_types(df):
    df["tournament_type"] = df["name"].apply(tournament_type_finder)
    return df


class ABG_Stats:

    def __init__(self, matches, playersdf, rampup = 400):
        self.matches = matches
        self.players = playersdf.to_dict()
        self.elo = ELO(rampup)
        self.first_row_done = False

    def change_player_elo(self, player_name, new_elo, xp, date):
        self.players["ELO"][player_name] = new_elo
        self.players["xp"][player_name] += xp

    def find_by_name(self, name):
        out = {}
        for k, v in self.players.items():
            out[k] = v[name]
        return out

    def standard_elo_calc(self):
        self.matches[['player1_ELO_change','player2_ELO_change', "player1_ELO", "player2_ELO"]] = self.matches.apply(self.set_elo, axis=1)

    def export(self, output_directory):

        playersdf = pd.DataFrame().from_dict(self.players)
        playersdf.index.name = "player_name"

        l.info("Processed {} matches".format(len(self.matches)))
        l.info("Exported ELO data on {} players".format(len(playersdf)))


        playersdf.sort_values("ELO", inplace=True, ascending=False)
        playersdf.to_csv(open(output_directory + "/players_elo.csv", "w"))
        self.matches.to_csv(open(output_directory + "/match_log.csv", "w"))

    def set_elo(self, row):
        if not hasattr(self.set_elo.__func__,"counter"):
            self.set_elo.__func__.counter = 0
        self.set_elo.__func__.counter += 1

        try:
            length = row["match-length"]
        except ValueError:
            print("I am afraid {} is not a number".format(row["match-length"]))
            return pd.Series([0,0])

        if (math.isnan(length)):
            print("I am afraid {} is not a number".format(row["match-length"]))
            return pd.Series([0,0])
        # @TODO: When we want to store more stats on players
        # _players = {"player1": {}, "player2": {}}
        # for k in row.keys():
        #     m = re.search("(player[1-2])-([a-zA-Z0-9\-_]+)", k)
        #     if (m):
        #         _players[m.group(1)][m.group(2)] = row[k]
        # player1 = _players["player1"]
        # player2 = _players["player2"]

        player1 = {"name": row['player1-name'], "score": row['player1-score']}
        player2 = {"name": row['player2-name'], "score": row['player2-score']}

        player1.update(self.find_by_name(player1["name"]))
        player2.update(self.find_by_name(player2["name"]))

        l.debug("Recording match between {} and {} with ELOs {} and {}".format(
        player1["name"], player2["name"], float(player1["ELO"]), float(player2["ELO"])))

        #figure out who is the winner
        if player1["score"] > player2["score"]:
            winning_player = "player1"
            player1_change, player2_change = self.elo.compute_change(player1["ELO"],player2["ELO"], length, player1["xp"], player2["xp"])
        else:
            winning_player = "player2"
            player2_change, player1_change = self.elo.compute_change(player2["ELO"],player1["ELO"], length, player2["xp"], player1["xp"])

        player1_new_elo = float(player1["ELO"]) + player1_change
        player2_new_elo = float(player2["ELO"]) + player2_change

        self.change_player_elo(player1["name"], player1_new_elo, length, row["match-completed-at"])
        self.change_player_elo(player2["name"], player2_new_elo, length, row["match-completed-at"])

        l.debug("Recorded match between {} and {} changed ELOs by {} and {}".format(
        player1["name"], player2["name"], float(player1_change), float(player2_change)))

        return pd.Series([player1_change, player2_change, player1_new_elo, player2_new_elo])

    def add_running_win_loss_columns(self):
        self.matches["winner"] = ""
        self.matches["winner_elo_in"] = 0
        self.matches["winner_elo"] = 0
        self.matches["winner_elo_change"] = 0

        self.matches["loser"] = ""
        self.matches["loser_elo_in"] = 0
        self.matches["loser_elo"] = 0
        self.matches["loser_elo_change"] = 0

        self.matches["winner"] = self.matches.loc[self.matches["player1_ELO_change"] > 0]["player1-name"]
        self.matches["winner_elo"] = self.matches.loc[self.matches["player1_ELO_change"] > 0]["player1_ELO"]
        self.matches["winner_elo_change"] = self.matches.loc[self.matches["player1_ELO_change"] > 0]["player1_ELO_change"]

        self.matches["winner"][self.matches["player2_ELO_change"] > 0] = self.matches.loc[self.matches["player2_ELO_change"] > 0]["player2-name"]
        self.matches["winner_elo"][self.matches["player2_ELO_change"] > 0] = self.matches.loc[self.matches["player2_ELO_change"] > 0]["player2_ELO"]
        self.matches["winner_elo_change"][self.matches["player2_ELO_change"] > 0] = self.matches.loc[self.matches["player2_ELO_change"] > 0]["player2_ELO_change"]

        self.matches["loser"] = self.matches.loc[self.matches["player1_ELO_change"] < 0]["player1-name"]
        self.matches["loser_elo"] = self.matches.loc[self.matches["player1_ELO_change"] < 0]["player1_ELO"]
        self.matches["loser_elo_change"] = self.matches.loc[self.matches["player1_ELO_change"] < 0]["player1_ELO_change"]

        self.matches["loser"][self.matches["player2_ELO_change"] < 0] = self.matches.loc[self.matches["player2_ELO_change"] < 0]["player2-name"]
        self.matches["loser_elo"][self.matches["player2_ELO_change"] < 0] = self.matches.loc[self.matches["player2_ELO_change"] < 0]["player2_ELO"]
        self.matches["loser_elo_change"][self.matches["player2_ELO_change"] < 0] = self.matches.loc[self.matches["player2_ELO_change"] < 0]["player2_ELO_change"]

        self.matches["winner_elo_in"] = self.matches["winner_elo"] - self.matches["winner_elo_change"]
        self.matches["loser_elo_in"] = self.matches["loser_elo"] - self.matches["loser_elo_change"]

# abg = pd.read_csv('data/abg.csv', parse_dates=["match-completed-at", "created-at", "completed-at", "match-completed-at", "created-at"], dtype={"match-scores-csv": str, "predict-the-losers-bracket": str, "start-at": str,"match-underway-at": str })
# abg = clean_matches(abg)
# # Finds the "type" or group of tournament
# abg = set_tournament_types(abg)
# abg = abg.loc[abg["match-completed-at"] > datetime.datetime(2014, 10, 29).strftime("%Y-%m-%d")]
# players_df = build_players(abg)
# #players2_df = players1_df.copy()
# abg1 = ABGStats(abg.copy(), players_df.copy())
#
# #ELO Calcs across all matches
# abg1.standard_elo_calc()
# abg1.add_running_win_loss_columns()
# abg1.export(data_dir + "/all_matches")
#
# abgdf_2 = abg.copy()
# abgdf_2 = abgdf_2[abgdf_2["tournament_type"] != 'Champion and Challenger']
# abg2 = ABGStats(abgdf_2, players_df.copy())
# abg2.standard_elo_calc()
# abg2.add_running_win_loss_columns()
# abg1.export(data_dir + "/all_but_champ")
