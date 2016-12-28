import challonge
import asyncio
from challonge import Account
from pprint import pprint as pp
import logging
import dateutil.parser
import datetime
import pytz
utc=pytz.UTC
import asyncio
from time import sleep

l = logging.getLogger('abg')
l.setLevel("DEBUG")

class ABG_Challonge:

    def __init__(self, username, api_key, **params):
        if 'test' in params and (params['test'] == True):
            self.test=True
            l.info("starting in test mode")
        else:
            self.test=False
            l.info("starting in live mode")
        self.account=Account(username, api_key)
        self.participants={}
        # Stores counts for reporting
        self.counts = {"tournaments":0, "matches_not_added":0, "matches_added":0}

    async def get_all_tournaments(self, **params):
        l.debug(str(params))
        self.tournaments=await self.account.tournaments.index(**params)
        self.counts["tournaments"] = len(self.tournaments)

    def add_prefix_to_dictionary(self, dictionary, prefix):
        new_dictionary={}
        for k, v in dictionary.items():
            new_dictionary[prefix + k] = v
        return new_dictionary

    async def flatten(self, **params):
        rows = []
        for t in self.tournaments:
            try:
                l.debug("Geting {}".format(t["id"]))
                sleep(.1)
                tournament = await self.account.tournaments.show(t["id"], include_matches="1", include_participants="1")
            except RuntimeError:
                l.error("failed while getting https://api.challonge.com/v1/tournaments/{}.xml".format(t["id"]), exc_info=True)
                continue
            participants = {}

            # @NOTE: THis might be a problem if IDs clash... unlikely
            for player in tournament["participants"]:
                player = { k: player[k] for k in ["id", "name", "group-player-ids"] }
                # tournament["participants"] = { k: tournament[your_key] for k in ["id", "name", "matches", "participants"] }
                if tournament["group-stages-enabled"] == True:
                    if len(player["group-player-ids"]) > 0:
                        try:
                            group_player_id_map = player["group-player-ids"][0]
                            participants[group_player_id_map] = player
                        except:
                            print(group_player_id_map)
                            pp(player)

                participants[player["id"]] = player

            for match in tournament["matches"]:

                if (match["state"] != "complete"):
                    continue
                if "start_from_date" in params and params["start_from_date"] is not None:
                    if (match["updated-at"].astimezone(utc) <= params["start_from_date"]):
                        self.counts["matches_not_added"] += 1
                        continue
                self.counts["matches_added"] += 1
                row = {"DQ":False, "DQ_text": ""}

                tournament_fields = { k: tournament[k] for k in ["id", "name", "group-stages-enabled", "created-at", "completed-at", "state"] }
                row.update(tournament_fields)

                # @TODO: DL the attachment and store it (probably when we switch to SQL)
                # Process the DQ in stats
                # @TODO: Support other attachments
                if (("attachment-count" in match) and (match["attachment-count"] not in [None,0])):
                    attachments = await self.account.attachments.index(tournament["id"], match["id"])
                    for a in attachments:
                        if (await self.check_for_dq(a) != False):
                            row["DQ"] = True
                            row["DQ_text"] = a["description"]

                match_fields = { k: match[k] for k in ["id", "state", "completed-at", "updated-at", "scores-csv"] }
                row.update(self.add_prefix_to_dictionary(match_fields, "match-"))
                try:
                    row["player1-name"] = participants[match['player1-id']]["name"]
                    row["player2-name"] = participants[match['player2-id']]["name"]
                    ##Gets all match and player data, adds prefix to it
                    # row.update(self.add_prefix_to_dictionary(
                    #     participants[match['player1-id']], "player1-"))
                    # row.update(self.add_prefix_to_dictionary(
                    #     participants[match['player2-id']], "player2-"))

                except:
                    ## Some matches seem to be empty
                    l.warn("Unable to find participants for https://api.challonge.com/v1/tournaments/{}/matches/{}.json".format(t["id"],match["id"]))
                    l.warn("Participant IDs {}".format(participants.keys()))
                    l.warn("IDs searching for {} and {}".format(match["player1-id"], match["player2-id"]))
                    continue
                if ("exclude_fields" in params):
                    exclude_fields=params['exclude_fields']
                    row={key: value for key, value in row.items() if key not in exclude_fields}

                # Convert all dates to UTC
                for k,v in row.items():
                    if type(v) is datetime.datetime:
                        row[k] = v.astimezone(utc)
                rows.append(row)
        return rows

    async def check_for_dq(self, attachment):
        if ("description" in attachment and attachment["description"] != None and ("ABGDQ" in attachment["description"])):
            return True
        return False

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
            if (moved > 100):
                return;
            if (tournament["subdomain"] == subdomain):
                l.info("not moving {}".format(tournament["url"]))
            else:
                await self.move_tournament(tournament, subdomain)
                moved += 1

        l.info("moved {}".format(moved))
