import patreon
import discord as dc

# command line args
import sys
import asyncio

# local file to just wrap the patrons.json file
import patrons

from time import sleep
from os.path import isfile

# give the patreon token first, then discord token on CLI, lastly discord appid
# example:
# ./fetch.py <patreon_token> <discord_token> <discord_appid>
# ./fetch.py dnwif82374y5gf 4985vrniwuu4n53b99 8324984325
# These ^^^ are not the real tokens/appid of course!
#
# alternatively just create patreon_token.txt and discord_token.txt and discord_appid.txt

patreon_token_filename = "patreon_token.txt"
discord_token_filename = "discord_token.txt"
discord_appid_filename = "discord_appid.txt"

patrons_filepath = "./files/patrons.json"

official_amt = 200
enthusiastic_amt = 500
amazing_amt = 1000
legendary_amt = 2500

def patreon_token() -> str:
    if len(sys.argv) > 1:
        print("Token was given on command line")
        token = sys.argv[1]
    elif isfile(patreon_token_filename):
        print(f"Token was found in {patreon_token_filename}")
        with open(patreon_token_filename, "r") as f:
            token = f.readline()
    else:
        print("Token was not found")
        token = None

    if token == None or len(token) == 0:
        print("Token is empty")
        exit(1)
    return token

def discord_token() -> str:
    if len(sys.argv) > 2:
        print("Token was given on command line")
        token = sys.argv[2]
    elif isfile(discord_token_filename):
        print(f"Token was found in {discord_token_filename}")
        with open(discord_token_filename, "r") as f:
            token = f.readline()
    else:
        print("Token was not found")
        token = None

    if token == None or len(token) == 0:
        print("Token is empty")
        exit(1)
    return token

def discord_appid() -> str:
    if len(sys.argv) > 3:
        print("Appid was given on command line")
        token = sys.argv[3]
    elif isfile(discord_appid_filename):
        print(f"Appid was found in {discord_appid_filename}")
        with open(discord_appid_filename, "r") as f:
            token = f.readline()
    else:
        print("Appid was not found")
        token = None

    if token == None or len(token) == 0:
        print("Appid is empty")
        exit(1)
    return token

async def get_discord_name(client, patron) -> (None | str):
    socials = patron.attribute('social_connections')
    discord = socials['discord']
    if discord:
        discord_user_id = int(discord['user_id'])
        user = await client.fetch_user(discord_user_id)
        if user:
            return user.name
    return None
        
async def get_name(client, patron) -> str:
    name = await get_discord_name(client, patron)
    if name != None and name != "":
        return name
    campaign = patron.attribute('campaign')
    if campaign:
        vanity = campaign.attribute('vanity')
        if vanity:
            return vanity

    first_name = patron.attribute('first_name')
    last_name = patron.attribute('last_name')
    # don't include full last name if we can help it
    if len(last_name) > 0:
        return f"{first_name} {last_name[0:1]}."
    else:
        return first_name

async def main():
    patreon_api = patreon.API(patreon_token())
    discord_api = dc.Client()
    await discord_api.login(discord_token())

    campaign = patreon_api.fetch_campaign()
    campaign_id = campaign.data()[0].id()

    all_pledges = []
    cursor = None

    print("Fetching all patreon pledges")
    while True:
        pledges = patreon_api.fetch_page_of_pledges(
            campaign_id, 25,
            cursor=cursor,
            fields = {'pledge': ['total_historical_amount_cents', 'declined_since']}
            )
        cursor = patreon_api.extract_cursor(pledges)
        all_pledges += pledges.data()
        if not cursor:
            break
    
    usable_pledges = []

    for pledge in all_pledges:
        declined = pledge.attribute('declined_since')
        
        all_time_amt = pledge.attribute('total_historical_amount_cents')
        monthly_amt = 0
        
        if pledge.relationships()['reward']['data']:
            monthly_amt = pledge.relationship('reward').attribute('amount_cents')
        
        patron = pledge.relationship('patron')
        name = await get_name(discord_api, patron)
        tier = None

        if monthly_amt >= enthusiastic_amt and monthly_amt < amazing_amt:
            tier = "enthusiastic"
        elif monthly_amt >= amazing_amt and monthly_amt < legendary_amt:
            tier = "amazing"
        elif monthly_amt >= legendary_amt:
            tier = "legendary"

        if tier and not declined:
            usable_pledges.append({
                    "tier": tier,
                    "name": name,
                    "amount": monthly_amt,
                    "alltime": all_time_amt,
                })
        else:
            print(f"A user was declined")

    usable_pledges.sort(key=lambda x: x['alltime'], reverse=True)

    # close discord api
    await discord_api.close()

    patronfile = patrons.read(patrons_filepath)

    patronfile.enthusiastic.clear()
    patronfile.amazing.clear()
    patronfile.legendary.clear()

    for pledge in usable_pledges:
        tier = pledge['tier']
        if tier == "enthusiastic":
            patronfile.enthusiastic.append(pledge['name'])
        elif tier == "amazing":
            patronfile.amazing.append(pledge['name'])
        elif tier == "legendary":
            patronfile.legendary.append(pledge['name'])
            
    patronfile.write()


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except:
        # if there is any exception, exit with an exit code
        print("Exception ocurred in main async function")
        exit(2)