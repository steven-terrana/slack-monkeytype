from tinydb import where


class Settings:
    "represents the settings view"

    defaults = {
        "duration": {"text": {"type": "plain_text", "text": "60s"}, "value": "time-60"},
        "difficulty": {
            "text": {"type": "plain_text", "text": "normal"},
            "value": "normal",
        },
        "punctuation": [],
    }

    def __init__(self, db, client, logger):
        self.table = db.table("settings")
        self.client = client
        self.logger = logger

    async def open(self, view_id, trigger_id):
        "opens the settings view"
        # check if the user changed the default settings before
        # if they haven't, just use the defaults
        saved = self.table.get(where("view_id") == view_id)
        settings = saved if saved is not None else self.defaults
        await self.client.views_push(
            trigger_id=trigger_id,
            view={
                "type": "modal",
                "callback_id": "settings",
                "notify_on_close": True,
                "title": {
                    "type": "plain_text",
                    "text": ":gear: Settings",
                    "emoji": True,
                },
                "submit": {"type": "plain_text", "text": "Apply"},
                "blocks": self.build_view_blocks(settings),
            },
        )

    def build_view_blocks(self, settings):
        "construct the view blocks using the initial options provided by settings"
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Filters", "emoji": True},
            },
            {
                "type": "input",
                "element": {
                    "type": "static_select",
                    "action_id": "duration",
                    "initial_option": settings["duration"],
                    "placeholder": {
                        "type": "plain_text",
                        "emoji": True,
                        "text": "Duration",
                    },
                    "option_groups": [
                        {
                            "label": {"type": "plain_text", "text": "Time"},
                            "options": [
                                {
                                    "text": {"type": "plain_text", "text": "15s"},
                                    "value": "time-15",
                                },
                                {
                                    "text": {"type": "plain_text", "text": "30s"},
                                    "value": "time-30",
                                },
                                {
                                    "text": {"type": "plain_text", "text": "60s"},
                                    "value": "time-60",
                                },
                                {
                                    "text": {"type": "plain_text", "text": "120s"},
                                    "value": "time-120",
                                },
                            ],
                        },
                        {
                            "label": {"type": "plain_text", "text": "Words"},
                            "options": [
                                {
                                    "text": {"type": "plain_text", "text": "10"},
                                    "value": "words-10",
                                },
                                {
                                    "text": {"type": "plain_text", "text": "25"},
                                    "value": "words-25",
                                },
                                {
                                    "text": {"type": "plain_text", "text": "50"},
                                    "value": "words-50",
                                },
                                {
                                    "text": {"type": "plain_text", "text": "100"},
                                    "value": "words-100",
                                },
                            ],
                        },
                    ],
                },
                "label": {"type": "plain_text", "text": "Duration", "emoji": True},
            },
            {
                "type": "input",
                "element": {
                    "type": "static_select",
                    "action_id": "difficulty",
                    "initial_option": settings["difficulty"],
                    "placeholder": {
                        "type": "plain_text",
                        "emoji": True,
                        "text": "Difficulty",
                    },
                    "options": [
                        {
                            "text": {"type": "plain_text", "text": "normal"},
                            "value": "normal",
                        },
                        {
                            "text": {"type": "plain_text", "text": "expert"},
                            "value": "expert",
                        },
                        {
                            "text": {"type": "plain_text", "text": "master"},
                            "value": "master",
                        },
                    ],
                },
                "label": {"type": "plain_text", "text": "Difficulty", "emoji": True},
            },
            {
                "type": "input",
                "optional": True,
                "element": {
                    "type": "checkboxes",
                    "action_id": "punctuation",
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Enabled",
                                "emoji": True,
                            },
                            "value": "punctuation",
                        }
                    ],
                },
                "label": {"type": "plain_text", "text": "Punctuation", "emoji": True},
            },
        ]
        # unfortunately, for checkboxes, you can't set the initial_options to be []
        # so we have to do this hack where we only add "initial_options" if the
        # punctuation checkbox is selected.
        if bool(settings["punctuation"]):
            blocks[-1]["element"]["initial_options"] = settings["punctuation"]

        return blocks

    def save(self, view_id, selections):
        "persist the user's configured settings"
        values = {}
        for value in selections.values():
            values.update(value)
        self.table.upsert(
            {
                "view_id": view_id,
                "duration": values["duration"]["selected_option"],
                "difficulty": values["difficulty"]["selected_option"],
                "punctuation": values["punctuation"]["selected_options"],
            },
            where("view_id") == view_id,
        )

    def remove(self, view_id):
        """
        forget the user's configured settings
        this should only happen when the root view is closed
        """
        self.table.remove(where("view_id") == view_id)

    def build_fragment(self, selections):
        """
        parses the selections from the settings view submission into a query fragment
        that can be used to filter the bests table
        """
        values = {}
        for value in selections.values():
            values.update(value)
        (category, duration) = values["duration"]["selected_option"]["value"].split("-")
        difficulty = values["difficulty"]["selected_option"]["value"]
        punctuation = bool(len(values["punctuation"]["selected_options"]))
        return {
            "category": category,
            "duration": duration,
            "difficulty": difficulty,
            "language": "english",
            "punctuation": punctuation,
        }
