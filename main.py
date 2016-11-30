import sys,os
import challonge
import asyncio
from challonge import Account
import csv
from pprint import pprint as pp
import logging
import configparser

l = logging.getLogger("abg")
l.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
l.addHandler(ch)


import getopt


class ABG:

    def __init__(self, account, **params):
        if 'test' in params and (params['test'] == True):
            self.test=True
            l.info("starting in test mode")
        else:
            self.test=False
            l.info("starting in live mode")

        self.account=account
        self.participants={}

    async def get_all_tournaments(self, **params):
        l.debug(str(params))
        self.tournaments=await self.account.tournaments.index(**params)

    async def get_participants(self, tournament):
        participants=await account.participants.index(tournament["id"])
        for participant in participants:
            self.participants[participant['id']]=participant

    async def get_matches(self, tournament, **params):
        params['state']="complete"
        return await account.matches.index(tournament['id'], **params)

    def add_prefix_to_dictionary(self, dictionary, prefix):
        new_dictionary={}

        for k, v in dictionary.items():
            new_dictionary[prefix + k]=v
        return new_dictionary

    async def flatten(self, writer, **params):
        rows=[];
        for tournament in self.tournaments:
            await abg.get_participants(tournament)
            for match in await self.get_matches(tournament):
                row={}
                row.update(tournament)

                if ((match['player1-id'] or match['player2-id']) not in self.participants):
                    # pp("There was an error getting players")
                    # pp(tournament)
                    # pp(match)
                    continue


                row.update(self.add_prefix_to_dictionary(match, "match-"));
                row.update(self.add_prefix_to_dictionary(
                    self.participants[match['player1-id']], "player1-"))
                row.update(self.add_prefix_to_dictionary(
                    self.participants[match['player2-id']], "player2-"))

                if ("exclude_fields" in params):
                    exclude_fields=params['exclude_fields']
                    row={key: value for key, value in row.items()
                                                                if key not in exclude_fields}
                writer.addRow(row)

        return rows

    async def move_tournament(self, tournament, subdomain):


        l.info("moving {}, currently on {} to {} subdomain".format(tournament["url"], tournament["subdomain"], subdomain))
        if (self.test == False):
            return await self.account.tournaments.update(tournament["id"], subdomain = subdomain)
        else:
            return True


    async def move_tournaments(self, subdomain, **params):
        l.info(params)
        moved = 0

        # Blocking call which returns when the hello_world() coroutine is done
        await self.get_all_tournaments(**params)
        l.info("attempting to move {} tournaments".format(len(self.tournaments)))
        for tournament in self.tournaments:
            if (tournament["subdomain"] == subdomain):
                l.info("not moving {}".format(tournament["url"]))
            else:
                await self.move_tournament(tournament, subdomain)
                moved += 1

        l.info("moved {}".format(moved))






class ABG_CSV_Writer:

    def __init__(self, filename):
        f=open(filename, 'w');
        self.writer=csv.DictWriter(f, ["stupid"])
        self.headers=None

    def addHeaders(self, keys):

        self.writer.fieldnames=keys
        self.writer.writeheader()
        self.headers=keys


    def addRow(self, row = {}):
        if (self.headers == None):
            self.addHeaders(row.keys())
        self.writer.writerow(row)



def main(argv):

    if os.path.exists('./abg.ini'):
        config=configparser.ConfigParser({"abg":{'output_file': '/tmp/abg_out.csv'}})
        config.read('./abg.ini')
        username=config["challonge"]["username"]
        api_key=config["challonge"]["api_key"]
        pp(config.defaults())
        output_file=config.get("abg","output_file")

    try:
      opts, args= getopt.getopt(argv, "k:u:o:", ["username=", "key="])
    except getopt.GetoptError:
        print('abg.py -k key -u user -o outputfile COMMAND')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-u", "--username"):
            username=arg
        elif opt in ("-k", "--key"):
            api_key=arg
        elif opt in ('-o'):
            output_file=arg

    if (api_key is None):
        print("Set the CHALLONGE_API_KEY environment variable (export CHALLONGE_API_KEY=xyz)")
        sys.exit()

    if (username is None):
        print("Set the CHALLONGE_USERNAME environment variable (export CHALLONGE_USERNAME=me@example.com)")
        sys.exit()

    # Tell pychallonge about your [CHALLONGE! API
    # credentials](http://api.challonge.com/v1).
    account=Account(username, api_key)
    loop=asyncio.get_event_loop()

    if (len(args) == 0):
        raise Exception("Provide a command (move | movetest | rip)")

    if (args[0] == "move"):
        abg=ABG(account)
        loop.run_until_complete(abg.move_tournaments("allbackgammon", created_after = "2016-09-01",subdomain = ""))
    elif(args[0] == "movetest"):
        abg=ABG(account, test=True)
        loop.run_until_complete(abg.move_tournaments("allbackgammon"))
    elif(args[0] == "rip"):
        writer=ABG_CSV_Writer("/tmp/out.csv")
    else:
        raise Exception("Provide a command (move | movetest | rip)")


if __name__ == "__main__":
   main(sys.argv[1:])





exit()


loop.run_until_complete(abg.move_tournament(
    "allbackgammon", tournament_url="swissy33"))


# Blocking call which returns when the hello_world() coroutine is done
loop.run_until_complete(abg.get_all_tournaments(
    created_after="2016-09-01", subdomain=""))
pp(abg.tournaments)
exit()

loop.run_until_complete(abg.flatten(writer, exclude_fields=[
                        'description', 'description-source']))

loop.close()
exit()
