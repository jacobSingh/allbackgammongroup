import challonge
import asyncio
from challonge import Account
from pprint import pprint as pp
import logging
import dateutil.parser
import pytz
utc=pytz.UTC
import asyncio

l = logging.getLogger('abg')

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

    async def get_all_tournaments(self, **params):
        l.debug(str(params))
        self.tournaments=await self.account.tournaments.index(**params)

    async def get_participants(self, tournament):
        participants=await self.account.participants.index(tournament["id"])
        for participant in participants:
            self.participants[participant['id']]=participant

    async def get_matches(self, tournament, **params):
        params['state']="complete"
        return await self.account.matches.index(tournament['id'], **params)

    def add_prefix_to_dictionary(self, dictionary, prefix):
        new_dictionary={}
        for k, v in dictionary.items():
            new_dictionary[prefix + k]=v
        return new_dictionary

    async def flatten(self, writer, **params):
        rows=[];
        for tournament in self.tournaments:
            await self.get_participants(tournament)
            for match in await self.get_matches(tournament):
                if "start_from_date" in params and params["start_from_date"] is not None:
                    if (match["updated-at"] < utc.localize(params["start_from_date"])):
                        continue
                row={}
                row.update(tournament)

                if ((match['player1-id'] or match['player2-id']) not in self.participants):
                    l.warn("One of the players {} and {} not in participants list".format(match["player1-id"], match["player2-id"]))
                    # pp("There was an error getting players")
                    # pp(tournament)
                    # pp(match)
                    continue

                if ("has_attachment" in match and match["has_attachment"] == "true"):
                    attachments = await self.account.get_attachments(tournament["id"], match["id"])
                    for a in attachments:
                        if (await self.check_for_dq(a) != False):
                            row["DQ"] = a["description"]

                # Gets all match and player data, adds prefix to it
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

    async def check_for_dq(self, attachment):
        if ("ABGDQ" in attachment["description"]):
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
