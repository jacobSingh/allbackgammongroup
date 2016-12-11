import os

from flask import Flask
instance_path = os.path.abspath('../data')
app = Flask(__name__, instance_path=instance_path)

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
# from urlparse import urlparse
from pprint import pprint as pp
from io import BytesIO
import base64
import random

app.config.from_object('config.DevelopmentConfig')
#
# o = urlparse(app.request.url)
# print(o.hostname)  # will display '127.0.0.1'
# if (o.hostname == "localhost"):
#
# else:
#     app.config.from_object('configmodule.ProductionConfig')

@app.route("/")
def hello():

    players = pd.read_csv(app.open_instance_resource("all_but_champ/players_elo.csv"))
    experienced_players = players.loc[players["xp"] >= app.config["XP_THRESHOLD"]]

    experienced_players = experienced_players[["player_name", "ELO", "xp"]]


    funnynames = ["statocopia", "lies and damn lies", "nerdotica!", "useless facts and figures"]

    out = ""
    out += "<h1 style='color:blue'>Welcome to All Backgammon Group {}!</h1>".format(random.choice(funnynames))
    out += experienced_players.to_html()

    out += "<h2>ELO vs Experience</h2>"

    img = BytesIO()
    plt = sns.lmplot('ELO', 'xp', data=experienced_players, fit_reg=False)
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue())
    out += "<img src=\"data:image/png;base64,{}\" />".format(plot_url.decode('utf-8'))

    return out



if __name__ == "__main__":
    app.run(host='0.0.0.0')
