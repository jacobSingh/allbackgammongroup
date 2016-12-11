#!/usr/bin/env python
import abg
import getopt
import logging
import sys,os
import configparser
import getopt
from abg.stats import ABG_Stats, clean_matches, set_tournament_types, build_players, read_match_csv
import datetime

l = logging.getLogger('abg')
l.debug('Running data processing')

def parse_tournament_types(opt):
    options = opt.split(",")
    exclude = []
    include = []
    for i in options:
        if (options[0] == "-"):
            exclude.append(i[1:])
        else:
            include.append(i[1:])
    return (exclude,include)

def usage():
    sys.stderr.write('abg_elo.py -i [INCLUDE_TOURNAMENT] -e [EXCLUDE_TOURNAMENT] -f [INPUT_FILE] OUTPUT_DIR')

def main(argv):
    include_tournaments = []
    exclude_tournaments = []
    input_csv = None
    elo_rampup = 400
    if os.path.exists('./abg.ini'):
        config=configparser.ConfigParser()
        config.read('./abg.ini')

    try:
      opts, args= getopt.getopt(argv, "i:e:f:r:")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-f'):
            input_csv = open(arg, "r")
        elif opt in ('-i'):
            include_tournaments.append(arg)
        elif opt in ('-e'):
            include_tournaments.append(arg)
        elif opt in ('-r'):
            elo_rampup = arg

    # @todo: Add actions to clean and actions to computer ELO.
    # @TODO: consider making ELO calc generic

    output_dir = args[0]
    if not os.path.isdir(output_dir):
        raise Exception("Directory not found, provide OUTPUT DIR")

    if (input_csv is None):
        input_csv = sys.stdin

    #@TODO: move to base class
    abg = read_match_csv(input_csv)
    abg = clean_matches(abg)
    # Finds the "type" or group of tournament
    abg = set_tournament_types(abg)

    # Start date.... Should probably fix this in a param
    # @TODO: Param this.
    abg = abg.loc[abg["match-updated-at"] > datetime.datetime(2014, 10, 29).strftime("%Y-%m-%d")]
    players_df = build_players(abg)
    #players2_df = players1_df.copy()
    abg1 = ABG_Stats(abg.copy(), players_df.copy())

    #ELO Calcs across all matches
    abg1.standard_elo_calc()
    abg1.add_running_win_loss_columns()
    abg1.export(output_dir)
        #loop.run_until_complete(abg.move_tournaments("allbackgammon"))


if __name__ == "__main__":
   try:
       main(sys.argv[1:])
   except:
       usage()
       raise

exit()
