from tinydb import where, Query
from tinydb.operations import add


class User:
    "keeps track of registered users"

    def __init__(self, db, client, logger):
        self.table = db.table("users")
        self.client = client
        self.logger = logger

    async def open(self, trigger_id):
        "opens the register new typer view"
        await self.client.views_push(
            trigger_id=trigger_id,
            view={
                "title": {"type": "plain_text", "text": "Register User", "emoji": True},
                "callback_id": "register",
                "submit": {"type": "plain_text", "text": "Register", "emoji": True},
                "type": "modal",
                "close": {"type": "plain_text", "text": "Cancel", "emoji": True},
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "form",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "username",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Enter your Monkeytype Username...",
                            },
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Monkeytype Username",
                            "emoji": True,
                        },
                    }
                ],
            },
        )

    def register(self, username, channel):
        "add monkeytype user to users table"
        # if this user is already known, append to participating channels
        # otherwise, add the user to the table
        exists = bool(self.table.get(where("username") == username))
        if exists:
            self.table.update(add("channels", channel), where("username") == username)
        else:
            self.table.insert({"username": username, "channels": [channel]})

    def is_registered(self, username, channel):
        "check if the user is registered in a channel"
        return bool(
            self.table.get(
                (where("username") == username) & (Query().channels.any(channel))
            )
        )

    def get_all(self):
        "gets all monkeytype usernames that have been registered in any channel"
        return [user["username"] for user in self.table.all()]
