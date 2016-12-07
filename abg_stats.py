import pandas as pd
import numpy as np
from pprint import pprint as pp
import datetime
import re
import math
import logging
#%matplotlib inline
import matplotlib.pyplot as plt


logging.basicConfig(filename='/tmp/example.log')
l = logging.getLogger("abg")

l.setLevel(logging.WARN)
ch = logging.StreamHandler()

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
l.addHandler(ch)

def clean_matches(abg):
    abg = abg[["name", "match-id", "match-scores-csv", "completed-at", "match-updated-at", "created-at", "player1-name", "player2-name"]]
    abg.set_index("match-id", inplace=True)

    abg["match-updated-at"].fillna(abg["completed-at"],inplace=True)
    abg["match-updated-at"].fillna(abg["created-at"],inplace=True)

    abg.sort_values("match-updated-at", inplace=True)
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

class ELO:

    def __init__(self, rampup = 0):
        self.rampup = rampup

    def get_win_chance(self, elo1, elo2, length):
        exp = -1*(elo1-elo2) * np.sqrt(length)/2000
        return 1/(1+10**exp)

    def compute_change(self, elo_winner, elo_loser, length, winner_xp, loser_xp):

        elo_winner = int(elo_winner)
        elo_loser = int(elo_loser)
        points = 4 * np.sqrt(length)

        winner_change = (1 - self.get_win_chance(elo_winner, elo_loser, length)) * points
        loser_change = points * self.get_win_chance(elo_loser, elo_winner, length)

        if (type(loser_xp) is "NaN"):
            print("foo")
            exit()

        winner_change = winner_change * self.get_rampup_magnitude(int(winner_xp))
        loser_change = loser_change * self.get_rampup_magnitude(int(loser_xp))
        return (winner_change, loser_change * -1)

    def get_rampup_magnitude(self, xp):
        if (self.rampup > xp):
            return (((self.rampup+100) - xp) / 100)
        return 1

class ABGStats:

    def __init__(self, matches, players):
        self.matches = matches
        self.players = players
        self.elo = ELO(400)
        self.first_row_done = False

    def change_player_elo(self, player_name, new_elo, xp, date):
        self.players.loc[self.find_by_name(player_name).index,"ELO"] = new_elo
        self.players.loc[self.find_by_name(player_name).index,"xp"] = self.players.loc[self.find_by_name(player_name).index,"xp"] + xp
        #players.loc[find_by_name(player_name).index,"last_updated"] = date

    def find_by_name(self, name):
        return self.players.loc[self.players['player_name'] == name]

    def standard_elo_calc(self):
        self.matches[['player1_ELO_change','player2_ELO_change', "player1_ELO", "player2_ELO"]] = self.matches.apply(self.set_elo, axis=1)
        self.players.sort_values("ELO", inplace=True, ascending=False)

    def export(self, output_directory):
        self.players.to_csv(open(output_directory + "/players_elo.csv", "w"))
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
        player1["name"], player2["name"], player1["ELO"], player2["ELO"]))

        #figure out who is the winner
        if player1["score"] > player2["score"]:
            winning_player = "player1"
            player1_change, player2_change = self.elo.compute_change(player1["ELO"],player2["ELO"], length, player1["xp"], player2["xp"])
        else:
            winning_player = "player2"
            player2_change, player1_change = self.elo.compute_change(player2["ELO"],player1["ELO"], length, player2["xp"], player1["xp"])

        player1_new_elo = float(player1["ELO"]) + player1_change
        player2_new_elo = float(player2["ELO"]) + player2_change

        self.change_player_elo(player1["name"], player1_new_elo, length, row["match-updated-at"])
        self.change_player_elo(player2["name"], player2_new_elo, length, row["match-updated-at"])

        l.debug("Recorded match between {} and {} changed ELOs by {} and {}".format(
        player1["name"], player2["name"], player1_change, player2_change))

        l.debug("ELOs are now {}: {} and {}:{}".format(
        player1["name"], self.find_by_name(player1["name"])["ELO"], player2["name"], self.find_by_name(player2["name"])["ELO"]))


        if (self.set_elo.__func__.counter % 50 == 0):
            l.info("Rows: {}, ELO mean: {}".format(self.set_elo.__func__.counter,np.mean(self.players["ELO"])))

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


l.setLevel(logging.WARN)

abg = pd.read_csv('data/abg.csv', parse_dates=["match-updated-at", "created-at", "completed-at", "match-updated-at", "created-at"], dtype={"match-scores-csv": str, "predict-the-losers-bracket": str, "start-at": str,"match-underway-at": str })
abg = clean_matches(abg)
abg = abg.loc[abg["match-updated-at"] > datetime.datetime(2014, 10, 29).strftime("%Y-%m-%d")]

players_df = build_players(abg)

#players2_df = players1_df.copy()
abg1 = ABGStats(abg.copy(), players_df.copy())

abg1.standard_elo_calc()
abg1.add_running_win_loss_columns()
abg1.export("/tmp/all_matches")

abgdf_2 = abg.copy()
abgdf_2 = abgdf_2[abgdf_2["name"].str.contains("Challenger") == False]
abg2 = ABGStats(abgdf_2, players_df.copy())
abg2.standard_elo_calc()
abg2.add_running_win_loss_columns()
abg2.export("/tmp/all_but_champ")
