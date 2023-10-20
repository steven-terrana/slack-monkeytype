import re
import asyncio
import aiohttp
import os


class Monkeytype:
    "represents the monkeytype API"

    def __init__(self):
        self.ape_key = os.environ["APE_KEY"]

    def is_valid_username(self, username):
        "determines if a monkeytype username is valid"
        pattern = re.compile("^[a-zA-Z0-9_.-]*$")
        return bool(pattern.match(username))

    async def get_profile(self, session=None, username=None):
        "fetches a user's profile"
        # create a session if one wasn't provided
        should_close = False
        if session is None:
            session = aiohttp.ClientSession()
            should_close = True

        # get the profile
        resp = await session.get(
            f"https://api.monkeytype.com/users/{username}/profile",
            headers={"Authorization": f"ApeKey {self.ape_key}"},
        )
        json = await resp.json()

        # if session wasn't provided, close the one we created
        if should_close:
            await session.close()

        return json

    async def get_profiles(self, usernames):
        "fetches multiple user profiles"
        async with aiohttp.ClientSession() as session:
            tasks = [self.get_profile(session=session, username=u) for u in usernames]
            return await asyncio.gather(*tasks)

    async def profile_exists(self, username):
        "determines if a username corresponds to an existing profile"
        profile = await self.get_profile(username=username)
        return profile["message"] == "Profile retrieved"

    def get_profile_link(self, username):
        "returns a users public profile link"
        return f"https://monkeytype.com/profile/{username}"
