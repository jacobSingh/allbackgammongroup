import logging
l = logging.getLogger("abg")

import flask
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user
from flask import Markup
from flask import send_file
l.error("flask")
from abg_stats.extensions import login_manager
from abg_stats.public.forms import LoginForm
from abg_stats.user.forms import RegisterForm
from abg_stats.user.models import User
from abg_stats.utils import flash_errors
l.error("abg_stats")

import os
import matplotlib
matplotlib.use('agg')
l.error("matplot")

import pandas as pd
l.error("Pandas import")
import matplotlib.pyplot as plt
import numpy as np
l.error("Pandas and numpy")
# from urlparse import urlparse
from pprint import pprint as pp
from io import BytesIO
import base64
import random

l.error("Here")
import scipy.stats as stats
import scipy
from pandas_highcharts.core import serialize
l.error("Scipy and highcharts")
from flask_assets import Bundle, Environment
import math
l.error("Imports done")

blueprint = Blueprint('player', __name__, static_folder='../static', template_folder='../templates')

app = flask.current_app

def build_elo_dist_chart(df):
    return serialize(df, render_to="elo_stddev_chart", output_type="json", title="Compared to all players having experience over {}".format(app.config['XP_THRESHOLD']))

def build_elo_history(player_matches):
    chartdf = player_matches[['Date', 'Player ELO']]

    chartdf["Date"] = pd.DatetimeIndex(chartdf["Date"]).astype(int) / 1000 / 1000
    chartdf.set_index("Date", inplace=True)
    #pp(chartdf.index)
    #grouped = pd.groupby(chartdf,by=[chartdf.index.month,chartdf.index.year])["Player ELO"].mean()
    #chartdf["Player_ELO_rolling"] = pd.rolling_mean(chartdf["Player ELO"], window=5)
    #rouped = chartdf[["Player_ELO_rolling"]]
    return serialize(chartdf, render_to='elo_chart', output_type='json', title="ELO history")

def get_player_matches_df(matches, player_name):
    player_matches = matches[(matches['player1-name'] == player_name) | (matches['player2-name'] == player_name)]
    player_winner = matches[matches["winner"] == player_name]
    player_loser = matches[matches["loser"] == player_name]

    player_winner["player_elo_change"] = matches["winner_elo_change"]
    player_loser["player_elo_change"] = matches["loser_elo_change"]
    player_winner["player_elo"] = matches["winner_elo"]
    player_loser["player_elo"] = matches["loser_elo"]
    player_winner["W"] = 1
    player_winner["L"] = 0
    player_loser["W"] = 0
    player_loser["L"] = 1

    player_winner["opponent"] = player_winner["loser"]
    player_loser["opponent"] = player_loser["winner"]
    player_matches = pd.concat([player_winner, player_loser]).sort_values("match-completed-at")

    float_format = lambda x: "{%.0f}".format(x)
    player_matches["winner_elo_display"] = player_matches["winner_elo_in"].map(float_format) + " (" + player_matches["winner_elo"].map(float_format)  + ")"
    player_matches["loser_elo_display"] = player_matches["loser_elo_in"].map(float_format)  + " (" + player_matches["loser_elo"].map(float_format)  + ")"
    player_matches = player_matches[['match-completed-at', 'name', 'winner', 'loser', 'winner_elo_display', 'loser_elo_display', 'player_elo', "opponent", "W", "L"]]
    player_matches.columns = ['Date', 'Tournament', 'Winner', 'Loser', 'Winner ELO (result)', 'Loser ELO (result)', 'Player ELO', "Opponent", "W", "L"]

    return player_matches

@blueprint.route('/<player_name>')
def show_player_stats(player_name):

    player = {}
    # @TODO: remove the all_but_champ stuff and paramaterize
    players = pd.read_csv(os.path.join(app.config['DATA_DIR'], 'all_but_champ/players_elo.csv'))
    matches = pd.read_csv(os.path.join(app.config['DATA_DIR'], 'all_but_champ/match_log.csv'))

    player = dict(players[players["player_name"] == player_name].iloc[0])
    player_matches = get_player_matches_df(matches, player_name)

    formatters = {
        'Loser': lambda x: '<a href="{}">{}</a>'.format(url_for('player.show_player_stats', player_name=x), x),
        'Winner': lambda x: '<a href="{}">{}</a>'.format(url_for('player.show_player_stats', player_name=x), x),
    }

    pd.set_option('display.max_colwidth', 100)
    player_match_log = player_matches.copy()
    player_match_log = player_match_log[['Date', 'Tournament', 'Winner', 'Loser', 'Winner ELO (result)', 'Loser ELO (result)', 'Player ELO']]
    match_table = Markup(player_match_log.to_html(classes=["table-striped", "table"], index=False, formatters=formatters, escape=False, float_format='%.0f'))

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


    pp(player_matches.head())
    pt = pd.pivot_table(player_matches, index=["Opponent"], values=["W","L"], aggfunc=np.sum)
    pt["Total"] = pt["W"] + pt["L"]
    pt.sort_values("Total", inplace=True, ascending=False)

    pp(pt.head())

    # @TODO: Centralize this.
    formatters = {
        'Name': lambda x: '<a href="{}">{}</a>'.format(url_for('player.show_player_stats', player_name=x), x)
    }

    top_opponents = Markup(pt.head(10).to_html(index=True, classes=["table-striped", "table"], escape=False,formatters = formatters))

    return render_template('player.html', player=player, match_table=match_table, elo_chart=chart, elo_stddev_chart=elo_stddev_chart, top_opponents=top_opponents)
