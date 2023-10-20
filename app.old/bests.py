from tinydb import Query
from monkeytype import Monkeytype


class Bests:
    "keeps track of registered users personal bests"

    def __init__(self, db):
        self.table = db.table("bests")

    async def fetch_and_save(self, username):
        "fetches user's personal bests and writes to table"
        m = Monkeytype()
        profile = await m.get_profile(username=username)
        data = self.normalize_profile_data(profile)
        self.table.insert_multiple(data)

    def normalize_profile_data(self, profile):
        "flattens and enriches personal bests data"
        flattened = []
        bests = profile["data"]["personalBests"]
        for category in bests:
            for duration in bests[category]:
                for best in bests[category][duration]:
                    best["category"] = category
                    best["duration"] = duration
                    best["user"] = profile["data"]["name"]
                    flattened.append(best)
        return flattened

    def get(self, fragment):
        return self.table.search(Query().fragment(fragment))

    def overwrite(self, data):
        "overwrites all personal bests data"
        self.table.truncate()
        self.table.insert_multiple(data)
