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
from nvd3 import lineChart

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

    players = pd.read_csv(os.path.join(app.config['DATA_DIR'], 'all_but_champ/players_elo.csv'))
    matches = pd.read_csv(os.path.join(app.config['DATA_DIR'], 'all_but_champ/match_log.csv'))
    player_matches = matches[(matches['player1-name'] == player_name) | (matches['player2-name'] == player_name)]
    player_matches['ELO'] = player_matches.loc[player_matches['player1-name'] == player_name]['player1_ELO']
    player_matches['ELO'][player_matches['player2-name'] == player_name] = player_matches.loc[player_matches['player2-name'] == player_name]['player2_ELO']
    player_matches = player_matches[['match-updated-at', 'name', 'winner','loser', 'winner_elo_in', 'loser_elo', 'ELO']]
    player_matches.columns=['Date', 'Tournament', 'Winner', 'Loser', 'Winner ELO', 'Loser ELO', 'Player ELO']
    player = dict(players.loc[player_name])

    # @TODO: fix this column name
    player['name'] = player['player_name']
    match_table = Markup(player_matches.to_html(index=False, float_format='%.0f'))

    date_series = (pd.DatetimeIndex(player_matches['Date']).astype(int) / 1000 / 1000).tolist()

    chart = lineChart(name='ELO over time', x_is_date=True, width='1000', interpolate="basic")
    extra_serie = {'tooltip': {'y_start': 'START ', 'y_end': ' DONE'}}
    chart.add_serie(y=player_matches['Player ELO'].tolist(), x=date_series, name='ELO', extra=extra_serie)
    chart.buildhtml()

    return render_template('player.html', player=player, match_table=match_table, elo_chart=Markup(chart.htmlcontent))


def get_main_elo_table_html(df):
    df = df[['player_name', 'ELO', 'xp']]
    df.columns = ['Player', 'ELO', 'Experience']
    formatters = {
        'Player': lambda x: '<a href="{}">{}</a>'.format(url_for('abg.show_player_stats', player_name=x), x)
    }
    pd.set_option('display.max_colwidth', 100)
    return df.to_html(formatters=formatters, escape=False, float_format='%.0f')


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
