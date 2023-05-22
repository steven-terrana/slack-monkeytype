from tinydb import where
from tinydb.operations import set
from monkeytype import Monkeytype


class Leaderboard:
    default_query = {
        "category": "time",
        "duration": "60",
        "difficulty": "normal",
        "language": "english",
        "punctuation": False,
    }

    def __init__(self, db, bests, client, logger):
        self.table = db.table("leaderboards")
        self.bests = bests
        self.client = client
        self.logger = logger

    async def open(self, channel, trigger_id):
        "opens the root leaderboard view"
        blocks = self.build_view_blocks(self.default_query)
        response = await self.client.views_open(
            trigger_id=trigger_id,
            view={
                "type": "modal",
                "callback_id": "leaderboard",
                "notify_on_close": True,
                "title": {
                    "type": "plain_text",
                    "text": "Monkeytype",
                },
                "blocks": blocks,
            },
        )
        view = response["view"]["id"]
        self.table.insert(
            {"view": view, "channel": channel, "fragment": self.default_query}
        )

    async def update(self, view_id, fragment):
        """
        sets the leaderboard's filter fragment and refreshes the view
        """
        self.table.update(set("fragment", fragment), where("view") == view_id)
        await self.refresh(view_id)

    async def refresh(self, view_id):
        "updates the leaderboard based on the current query fragment"
        fragment = self.table.get(where("view") == view_id)["fragment"]
        await self.client.views_update(
            view_id=view_id,
            view={
                "type": "modal",
                "callback_id": "leaderboard",
                "notify_on_close": True,
                "title": {
                    "type": "plain_text",
                    "text": "Monkeytype Leaderboard",
                },
                "blocks": self.build_view_blocks(fragment),
            },
        )

    def build_view_blocks(self, fragment):
        "constructs the leaderboard"
        # define header block
        blocks = [
            {
                "type": "divider",
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": ":monkey_face: register a new typer!",
                            "emoji": True,
                        },
                        "action_id": "register",
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": ":gear: Settings",
                            "emoji": True,
                        },
                        "action_id": "settings",
                    },
                ],
            },
            {"type": "divider"},
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": ":trophy: Leaderboard",
                    "emoji": True,
                },
            },
        ]
        # add block describing filters
        filter_description = {"type": "context", "elements": []}
        filter_description["elements"].append(
            {
                "type": "mrkdwn",
                "text": f"*duration*: {fragment['duration']}{'s' if fragment['category'] == 'time' else ' words'}",
            }
        )
        filter_description["elements"].append(
            {"type": "mrkdwn", "text": f"*difficulty*: {fragment['difficulty']}"}
        )
        filter_description["elements"].append(
            {"type": "mrkdwn", "text": f"*punctuation*: {fragment['punctuation']}"}
        )
        blocks.append(filter_description)

        # separate header from results
        blocks.append({"type": "divider"})

        # filter the results table based on the query fragment
        filtered = self.bests.get(fragment)
        if len(filtered) == 0:
            blocks.append(
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "no results found with these filters",
                        }
                    ],
                }
            )
            return blocks

        # sort the results according to WPM with accuracy as the tiebreaker
        m = Monkeytype()
        sorted_results = sorted(filtered, key=lambda r: (-r["wpm"], -r["acc"]))
        for idx, result in enumerate(sorted_results):
            u = result["user"]
            w = result["wpm"]
            a = result["acc"]
            blocks += [
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"{self.get_position(idx)}<{m.get_profile_link(username=u)}|{u}> {w} wpm - {a}% accuracy",
                        }
                    ],
                }
            ]

        return blocks

    def get_position(self, idx):
        "return a medal emoji if you deserve a medal, otherwise return index"
        if idx == 0:
            return ":first_place_medal: "
        if idx == 1:
            return ":second_place_medal: "
        if idx == 2:
            return ":third_place_medal: "

        return f"{idx+1}. "

    def get_channel(self, view):
        "gets the channel where a leaderboard view was opened"
        return self.table.get(where("view") == view)["channel"]

    def remove(self, view):
        "deletes a closed view from the table"
        self.table.remove(where("view") == view)
