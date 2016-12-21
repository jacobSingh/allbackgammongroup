#!/usr/bin/env python
import abg
import asyncio
import getopt
import logging
import sys
import os
import configparser
import getopt
import dateutil.parser
import datetime
from abg.writers import CSV_Writer
from abg.challonge import ABG_Challonge
from pprint import pprint as pp

l = logging.getLogger('abg')
l.debug('Starting ABG Challonge')


def main(argv):
    try:

        opts, args = getopt.getopt(argv, "c:k:u:o:d:", ["username=", "key="])

        output_file = None
        username = None
        api_key = None
        created_after_date = None
        start_from_date = None

        inifile = "./abg.ini"
        for opt, arg in opts:
            if opt in ("-c"):
                inifile = arg
        if os.path.exists(inifile):
            config = configparser.ConfigParser()
            config.read(inifile)
            try:
                username = config["challonge"]["username"]
                api_key = config["challonge"]["api_key"]
                output_file = config.get("abg", "output_file")
            except configparser.NoOptionError:
                how_do_i_ignore = None

    except getopt.GetoptError:
        print('abg.py -c inifile -k key -u user -o outputfile COMMAND')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-u", "--username"):
            username = arg
        elif opt in ("-k", "--key"):
            api_key = arg
        elif opt in ('-o'):
            output_file = arg
            if (os.path.exists(output_file)):
                l.warn("Output file {} exists, appending to it.".format(output_file))
        elif opt in ('-d'):
            start_from_date = dateutil.parser.parse(arg)
            created_after_date = (start_from_date - datetime.timedelta(days=3)).strftime("%Y-%m-%d")
            l.info("Taking tournaments created less after {} and recording matches since {}".format(created_after_date, start_from_date))

            # = dateutil.parser.parse(arg)

    if (output_file is None):
        output_csv = sys.stdout
    else:
        output_csv = open(output_file, "a")

    if (api_key is None):
        print(
            "Set the CHALLONGE_API_KEY environment variable (export CHALLONGE_API_KEY=xyz)")
        sys.exit()

    if (username is None):
        print("Set the CHALLONGE_USERNAME environment variable (export CHALLONGE_USERNAME=me@example.com)")
        sys.exit()

    # Tell pychallonge about your [CHALLONGE! API
    # credentials](http://api.challonge.com/v1).

    loop = asyncio.get_event_loop()

    if (len(args) == 0):
        raise Exception("Provide a command (move | movetest | rip)")

    if (args[0] == "move"):
        abg = ABG_Challonge(username, api_key)
        loop.run_until_complete(abg.move_tournaments("allbackgammon"))
    elif(args[0] == "movetest"):
        abg = ABG_Challonge(username, api_key, test=True)
        loop.run_until_complete(abg.move_tournaments("allbackgammon"))
    elif(args[0] == "rip"):
        abg = ABG_Challonge(username, api_key)
        writer = CSV_Writer(output_csv)

        # @TODO Param this
        params = {'subdomain': "allbackgammon"}
        if (created_after_date):
            params['created_after'] = created_after_date
            params['created_before'] = "2016-10-01"

            #@TODO: Should I put this async and stream output?
            #@TODO: Yes, but it will require some refactoring which is a PITA
        loop.run_until_complete(abg.get_all_tournaments(**params))
        l.info("Downloaded {} tournaments".format(len(abg.tournaments)))
        # loop.run_until_complete(abg.get_all_participants())
        # l.info("Found {} players".format(len(abg.participants)))
        loop.run_until_complete(abg.flatten(writer, exclude_fields=[
                                'description', 'description-source'], start_from_date=start_from_date))
    else:
        raise Exception("Provide a command (move | movetest | rip)")


if __name__ == "__main__":
    main(sys.argv[1:])

exit()
