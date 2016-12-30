# -*- coding: utf-8 -*-
'''ABG Stats'''
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

blueprint = Blueprint('abg', __name__, static_folder='../static', template_folder='../templates')

app = flask.current_app
assets = Environment(app)

css = Bundle(
    'css/abg.style.css',
)
assets.register('all_css', css)


@blueprint.route('/', methods=['GET', 'POST'])
def home():
    """ABG Home Page."""
    app = flask.current_app
    matches = pd.read_csv(os.path.join(app.config['DATA_DIR'], 'all_but_champ/match_log.csv'))
    players = pd.read_csv(os.path.join(app.config['DATA_DIR'], 'all_but_champ/players_elo.csv'))
    experienced_players = players.loc[players['xp'] >= app.config['XP_THRESHOLD']]

    def win_record(v, matches):
        wins = len(matches[matches["winner"] == v["player_name"]])
        losses = len(matches[matches["loser"] == v["player_name"]])
        return pd.Series([wins, losses])

    experienced_players[["Wins", "Losses"]] = experienced_players.apply(win_record, axis=1, args=[matches])


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


@blueprint.route('/download_log', methods=['GET'])
def dl_match_log():
    return send_file(os.path.join(app.config['DATA_DIR'], 'all_but_champ/match_log.csv'),
                     mimetype='text/csv',
                     attachment_filename='match_log.csv',
                     as_attachment=True)

def get_main_elo_table_html(df):
    df = df[['player_name', 'ELO', 'xp', "Wins", "Losses"]]
    df["Win percentage"] = df["Wins"] / (df["Wins"] + df["Losses"]) * 100
    df.columns = ['Player', 'ELO', 'Experience',"Wins", "Losses","Win percentage"]
    formatters = {
        'Player': lambda x: '<a href="{}">{}</a>'.format(url_for('player.show_player_stats', player_name=x), x),
        #"Win percentage": lambda x: "{}%".format(x)
    }
    pd.set_option('display.max_colwidth', 100)
    return df.to_html(formatters=formatters, escape=False, float_format='%2.0f')
