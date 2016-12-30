# -*- coding: utf-8 -*-
'''ABG Stats'''
import flask
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user
from flask import Markup

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

blueprint = Blueprint('abg', __name__, static_folder='static', template_folder='templates')

app = flask.current_app
assets = Environment(app)

css = Bundle(
    'css/abg.style.css',
)
assets.register('all_css', css)

@blueprint.route('/player/<player_name>')
def show_player_stats(player_name):

    player = {}
    # @TODO: remove the all_but_champ stuff and paramaterize
    players = pd.read_csv(os.path.join(app.config['DATA_DIR'], 'all_but_champ/players_elo.csv'))
    matches = pd.read_csv(os.path.join(app.config['DATA_DIR'], 'all_but_champ/match_log.csv'))
    player_matches = matches[(matches['player1-name'] == player_name) | (matches['player2-name'] == player_name)]
    player_matches['ELO'] = player_matches.loc[player_matches['player1-name'] == player_name]['player1_ELO']
    player_matches['ELO'][player_matches['player2-name'] == player_name] = player_matches.loc[player_matches['player2-name'] == player_name]['player2_ELO']
    player_matches = player_matches[['match-completed-at', 'name', 'winner','loser', 'winner_elo_in', 'loser_elo', 'ELO']]
    player_matches.columns=['Date', 'Tournament', 'Winner', 'Loser', 'Winner ELO', 'Loser ELO', 'Player ELO']
    player = dict(players[players["player_name"] == player_name].iloc[0])

    # @TODO: fix this column name
    player['name'] = player['player_name']
    match_table = Markup(player_matches.to_html(index=False, float_format='%.0f'))

    date_series = (pd.DatetimeIndex(player_matches['Date']).astype(int) / 1000 / 1000).tolist()
    #chartdf = [date_series,player_matches["Player ELO"]]

    chartdf = player_matches[["Date", "Player ELO"]]
    chartdf["Date"] = pd.DatetimeIndex(chartdf["Date"]).astype(int) / 1000 / 1000
    chartdf.set_index("Date", inplace=True)
    #chartdf["Date"]

    chart = serialize(chartdf, render_to='elo_chart', output_type='json', title="ELO history")

    # Players stddist
    experienced_players = players.loc[players['xp'] >= app.config['XP_THRESHOLD']]
    h = sorted(experienced_players["ELO"].tolist())
    dist = stats.norm.pdf(h, 1500, np.std(h))
    df = pd.DataFrame({"ELO": h, "dist": dist})
    df = df.set_index("ELO")

    elo_stddev_chart = serialize(df, render_to="elo_stddev_chart", output_type="json", title="Compared to all players having experience over {}".format(app.config['XP_THRESHOLD']))
    # #f = display_charts(player_matches, kind="bar", title="Whatever")
    # #chart += f

    z_score = (player["ELO"] - np.mean(h)) / np.std(h)
    player["percentile"] = round(1 - scipy.stats.norm.sf(z_score) * 100)

    return render_template('player.html', player=player, match_table=match_table, elo_chart=chart, elo_stddev_chart=elo_stddev_chart)

@blueprint.route('/', methods=['GET', 'POST'])
def home():
    """ABG Home Page."""
    app = flask.current_app
    players = pd.read_csv(os.path.join(app.config['DATA_DIR'], 'all_but_champ/players_elo.csv'))
    experienced_players = players.loc[players['xp'] >= app.config['XP_THRESHOLD']]
    elo_table = get_main_elo_table_html(experienced_players)

    funnynames = ['statocopia', 'lies and damn lies', 'nerdotica!', 'useless facts and figures']

    img = BytesIO()
    chart = sns.lmplot('ELO', 'xp', data=experienced_players, fit_reg=False)
    chart.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue())

    abg_vars = {
        'sillyname': random.choice(funnynames),
        'table': Markup(elo_table),
        'scatter': Markup('<img src="data:image/png;base64,{}" />'.format(plot_url.decode('utf-8')))
    }

    return render_template('abg.html', **abg_vars)

@blueprint.route('/dqs', methods=['GET', 'POST'])
def dqs():
    """DQ page"""
    app = flask.current_app
    matches = pd.read_csv(os.path.join(app.config['DATA_DIR'], 'all_but_champ/match_log.csv'))
    dqs = matches[matches["DQ"] == True]
    dqs = dqs[['match-completed-at', 'name', 'winner','loser', 'DQ_text']]
    dqs.columns=['Data', 'Tournament', 'Winner', 'Loser', 'Description']

    pd.set_option('display.max_colwidth', 100)

    dq_vars = {
        "table": Markup(dqs.to_html())
    }

    return render_template('abg.html', **dq_vars)



def get_main_elo_table_html(df):
    df = df[['player_name', 'ELO', 'xp']]
    df.columns = ['Player', 'ELO', 'Experience']
    formatters = {
        'Player': lambda x: '<a href="{}">{}</a>'.format(url_for('abg.show_player_stats', player_name=x), x)
    }
    pd.set_option('display.max_colwidth', 100)
    return df.to_html(formatters=formatters, escape=False, float_format='%.0f')
