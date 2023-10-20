from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute

class UserModel(Model):
    """
    A MonkeyType User
    """

    class Meta:
        table_name = "users"
        host = "http://localhost:8000"
        write_capacity_units = 1
        read_capacity_units = 1


    monkeytype_profile = UnicodeAttribute(hash_key=True)
    slack_user = UnicodeAttribute()


# create a table if it doesn't exist
if not UserModel.exists():
    UserModel.create_table()


# create some users
a = UserModel('steven', slack_user='userA')
a.save()

b = UserModel('george', slack_user='userB')
b.save()

c = UserModel('goran', slack_user='nope')
c.save()

# iterate over all users
for user in UserModel.scan():
    print('----')
    for k,v in user.attribute_values.items():
        print(f"{k} = {v}")

# filter users