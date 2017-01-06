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

blueprint = Blueprint('tournaments', __name__, static_folder='../static', template_folder='../templates')

app = flask.current_app


@blueprint.route('/')
def tournaments():
    matches = pd.read_csv(os.path.join(app.config['DATA_DIR'], 'all_but_champ/match_log.csv'))
    tournaments = matches["tournament_type"].astype('category')
    pp(tournaments)
    return
    return render_template('tournaments.html', tournaments = tournaments)

@blueprint.route('/<tournament>')
def show_player_stats(player_name):

    return render_template('player.html', player=player, match_table=match_table, elo_chart=chart, elo_stddev_chart=elo_stddev_chart, top_opponents=top_opponents)
