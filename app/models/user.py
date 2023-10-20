from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute

class UserModel(Model):
    """
    A MonkeyType User
    """

    class Meta:
        table_name = "users"

    monkeytype_profile = UnicodeAttribute()