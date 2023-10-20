import os
from pathlib import Path
from dotenv import load_dotenv
from slack_bolt.logger import get_bolt_logger
from slack_bolt.async_app import AsyncApp
from slack_sdk import WebClient
from tinydb import TinyDB
import logging
from leaderboard import Leaderboard
from settings import Settings
from users import User
from bests import Bests
from monkeytype import Monkeytype
import time
import asyncio

# read secrets from the local ./.env file
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

# configure WebClient & Bolt
token = os.environ["SLACK_BOT_TOKEN"]
webClient = WebClient(token=token)
app = AsyncApp(token=token, signing_secret=os.environ["SLACK_SIGNING_SECRET"])

# configure Logging
logging.basicConfig(level=logging.INFO)

# initialize the DB
db = TinyDB(os.environ["DB_PATH"])

# configure utility classes
logger = get_bolt_logger(AsyncApp)
bests = Bests(db)
leaderboard = Leaderboard(db, bests, app.client, logger)
settings = Settings(db, app.client, logger)
users = User(db, app.client, logger)
monkeytype = Monkeytype()


# opens the leaderboard
@app.command("/monkeytype")
async def open_leaderboard(ack, body, command):
    "when user clicks opens the leaderboard"
    await ack()
    channel = command["channel_id"]
    # update_results(channel)
    trigger_id = body["trigger_id"]
    await leaderboard.open(channel, trigger_id)


# closes the leaderboard
@app.view_closed("leaderboard")
async def close_leaderboard(ack, body):
    "delete view from views and settings table"
    await ack()
    view_id = body["view"]["id"]
    leaderboard.remove(view_id)
    settings.remove(view_id)


# open register user view
@app.action("register")
async def open_register_user_view(ack, body):
    "when user clicks 'register a new typer'"
    await ack()
    trigger_id = body["trigger_id"]
    await users.open(trigger_id)


# submit user for registration
@app.view("register")
async def register_user(ack, body):
    "when user clicks 'register'"

    username = body["view"]["state"]["values"]["form"]["username"]["value"]

    # make sure the username is valid
    if not monkeytype.is_valid_username(username):
        await ack(
            response_action="errors", errors={"form": "That's not a valid username!"}
        )
        return

    # confirm the monkeytype profile actually exists
    if not await monkeytype.profile_exists(username):
        await ack(
            response_action="errors",
            errors={"form": f"monkeytype user '{username}' does not exist"},
        )
        return

    # check if this user is already registered in this channel
    view_id = body["view"]["root_view_id"]
    channel = leaderboard.get_channel(view_id)
    if users.is_registered(username, channel):
        await ack(
            response_action="errors",
            errors={"form": "this user is already registered!"},
        )
        return

    await ack()
    # register the user
    users.register(username, channel)
    # update bests table
    await bests.fetch_and_save(username)
    # update the leaderboard now that there's a new user
    await leaderboard.refresh(view_id)
    # notify the channel
    webClient.chat_postMessage(
        channel=channel,
        text=f"_crackles knuckles_ <{monkeytype.get_profile_link(username)}|{username}> has been added to the leaderboard",
    )


# open settings
@app.action("settings")
async def open_settings(ack, body):
    "when user clicks the settings button"
    await ack()
    view_id = body["view"]["root_view_id"]
    trigger_id = body["trigger_id"]
    await settings.open(view_id, trigger_id)


# submits settings
@app.view("settings")
async def submit_settings(ack, body):
    "when the user clicks Apply in settings view"
    await ack()
    view_id = body["view"]["root_view_id"]
    values = body["view"]["state"]["values"]
    fragment = settings.build_fragment(values)
    await leaderboard.update(view_id, fragment)
    settings.save(view_id, values)


async def background_tasks(_):
    "registers long running background tasks"
    asyncio.create_task(refresh_bests())


async def refresh_bests():
    "periodically refresh the user personal bests data"
    while True:
        tic = time.perf_counter()
        # get every registered users monkeytype profile
        u = users.get_all()
        profiles = await monkeytype.get_profiles(u)

        # get personal best data for each user
        data = []
        for profile in profiles:
            data += bests.normalize_profile_data(profile)

        # update the bests table
        bests.overwrite(data)
        toc = time.perf_counter()
        logger.info(
            "refreshed personal bests for %s users in %f seconds, will refresh again in 60 seconds", len(u), toc - tic
        )
        await asyncio.sleep(60)


if __name__ == "__main__":
    server = app.server(port=5000)
    server.web_app.on_startup.append(background_tasks)
    server.start()
