import flask
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user
from flask import Markup
from flask import send_file

from abg_stats.extensions import login_manager
from abg_stats.public.forms import LoginForm
from abg_stats.user.forms import RegisterForm
from abg_stats.user.models import User
from abg_stats.utils import flash_errors

import os
import matplotlib
matplotlib.use('agg')
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
# from urlparse import urlparse
from pprint import pprint as pp
from io import BytesIO
import base64
import random
import scipy.stats as stats
import scipy
from pandas_highcharts.core import serialize
from flask_assets import Bundle, Environment
import math

blueprint = Blueprint('player', __name__, static_folder='../static', template_folder='../templates')

app = flask.current_app

def build_elo_dist_chart(df):
    return serialize(df, render_to="elo_stddev_chart", output_type="json", title="Compared to all players having experience over {}".format(app.config['XP_THRESHOLD']))

def build_elo_history(player_matches):
    chartdf = player_matches[["Date", "Player ELO"]]
    chartdf["Date"] = pd.DatetimeIndex(chartdf["Date"]).astype(int) / 1000 / 1000
    chartdf.set_index("Date", inplace=True)
    return serialize(chartdf, render_to='elo_chart', output_type='json', title="ELO history")

def get_player_matches_df(matches, player_name):
    player_matches = matches[(matches['player1-name'] == player_name) | (matches['player2-name'] == player_name)]
    player_matches['ELO'] = player_matches.loc[player_matches['player1-name'] == player_name]['player1_ELO']
    player_matches['ELO'][player_matches['player2-name'] == player_name] = player_matches.loc[player_matches['player2-name'] == player_name]['player2_ELO']
    player_matches = player_matches[['match-completed-at', 'name', 'winner','loser', 'winner_elo_in', 'loser_elo', 'ELO']]
    player_matches.columns=['Date', 'Tournament', 'Winner', 'Loser', 'Winner ELO', 'Loser ELO', 'Player ELO']
    return player_matches

def get_top_opponents(player_matches, player_name):
    """ Returns a dict, keyed by name of dicts with wins and losses"""
    output = {}
    for k,i in player_matches.iterrows():
        if (i["Loser"] != player_name):
            if i["Loser"] not in output:
                output[i["Loser"]] = {"wins": 0, "losses": 0}
            output[i["Loser"]]["wins"] += 1
        else:
            if i["Winner"] not in output:
                output[i["Winner"]] = {"wins": 0, "losses": 0}
            output[i["Winner"]]["losses"] += 1
    return output

@blueprint.route('/<player_name>')
def show_player_stats(player_name):

    player = {}
    # @TODO: remove the all_but_champ stuff and paramaterize
    players = pd.read_csv(os.path.join(app.config['DATA_DIR'], 'all_but_champ/players_elo.csv'))
    matches = pd.read_csv(os.path.join(app.config['DATA_DIR'], 'all_but_champ/match_log.csv'))

    player = dict(players[players["player_name"] == player_name].iloc[0])

    player_matches = get_player_matches_df(matches, player_name)
    match_table = Markup(player_matches.to_html(index=False, float_format='%.0f'))
    chart = build_elo_history(player_matches)

    experienced_players = players.loc[players['xp'] >= app.config['XP_THRESHOLD']]
    elos = sorted(experienced_players["ELO"].tolist())
    dist = stats.norm.pdf(elos, 1500, np.std(elos))
    elo_dist_df = pd.DataFrame({"ELO": elos, "dist": dist})
    elo_dist_df = elo_dist_df.set_index("ELO")
    z_score = (player["ELO"] - np.mean(elos)) / np.std(elos)
    elo_stddev_chart = build_elo_dist_chart(elo_dist_df)
    player["percentile"] = round((1 - scipy.stats.norm.sf(z_score)) * 100)


    # @TODO: fix this column name
    player['name'] = player['player_name']

    stupid = []
    # This is stupid...
    for k,v in get_top_opponents(player_matches, player["name"]).items():
        row = v
        row["Name"] = k
        stupid.append(row)

    df = pd.DataFrame(stupid)
    df["total"] = df["wins"] + df["losses"]
    df.sort_values("total", inplace=True, ascending=False)

    # @TODO: Centralize this.
    formatters = {
        'Name': lambda x: '<a href="{}">{}</a>'.format(url_for('player.show_player_stats', player_name=x), x),
        #"Win percentage": lambda x: "{}%".format(x)
    }

    pd.set_option('display.max_colwidth', 100)
    top_opponents = Markup(df.head(20).to_html(escape=False,formatters = formatters))

    return render_template('player.html', player=player, match_table=match_table, elo_chart=chart, elo_stddev_chart=elo_stddev_chart, top_opponents=top_opponents)
