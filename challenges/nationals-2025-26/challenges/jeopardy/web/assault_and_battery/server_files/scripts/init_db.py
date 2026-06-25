import json
import os
import sys
from pathlib import Path

import django
from django.core import serializers as django_serializers
from faker import Faker

SERVER_FILES = Path(__file__).parent.parent.absolute()

# Ensure server_files/ is on sys.path
sys.path.insert(0, SERVER_FILES.as_posix())
_ = os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "reclaimer_central.settings"
)

django.setup()

from django.contrib.auth.models import User

from authentication import serializers as auth_serializers
from authentication.models import UserEncryptionKey
from bulletin import serializers as bulletin_serializers
from bulletin.models import Bulletin, BulletinPost, PostEncryptionKey

SCRIPT_DATA = SERVER_FILES / "scripts" / "data"
fake = Faker()
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "test-password")
with open(SCRIPT_DATA / "fortinet-2021_passwords.txt") as fd:
    USER_PASSWORD_LIST = fd.readlines()
with open(SCRIPT_DATA / "posts.json") as fd:
    BULLETIN_POSTS: dict[str, list[dict[str, object]]] = json.load(fd)
with open(SCRIPT_DATA / "admin_posts.json") as fd:
    ADMIN_BULLETIN_POSTS: dict[str, list[dict[str, object]]] = json.load(fd)

ADMIN_USER = {"username": "O-1", "password": ADMIN_PASSWORD}
USERS = [
    {
        "username": fake.user_name(),
        "password": fake.random_element(USER_PASSWORD_LIST),
    }
    for _ in range(20)
]


def main():
    register_serializer = auth_serializers.RegisterSerializer()
    bulletin_serializer = bulletin_serializers.BulletinSerializer()
    post_serializer = bulletin_serializers.BulletinPostSerializer()
    _ = register_serializer.create_admin(ADMIN_USER)
    for user_data in USERS:
        _ = register_serializer.create(user_data)

    for bulletin_name, posts in BULLETIN_POSTS.items():
        bulletin = bulletin_serializer.create({"title": bulletin_name})
        for post_data in posts:
            author_data = fake.random_element(USERS)
            author = User.objects.get(username=author_data.get("username"))
            post_with_meta = {
                **post_data,
                "bulletin": bulletin,
                "author": author,
            }
            if post_data.get("is_classified"):
                post_with_meta["password"] = author_data["password"]
            _ = post_serializer.create(post_with_meta)

    for bulletin_name, posts in ADMIN_BULLETIN_POSTS.items():
        bulletin = Bulletin.objects.get(title=bulletin_name)
        for post_data in posts:
            author = User.objects.get(username=ADMIN_USER.get("username"))
            post_with_meta = {
                **post_data,
                "bulletin": bulletin,
                "author": author,
            }
            if post_data.get("is_classified"):
                post_with_meta["password"] = ADMIN_USER.get("password")
            _ = post_serializer.create(post_with_meta)
    fixture_data = (
        list(User.objects.all())
        + list(UserEncryptionKey.objects.all())
        + list(Bulletin.objects.all())
        + list(BulletinPost.objects.all())
        + list(PostEncryptionKey.objects.all())
    )
    fixtures = json.loads(django_serializers.serialize("json", fixture_data))
    with open(SCRIPT_DATA / "fixtures.json", "w+") as out_file:
        json.dump(fixtures, out_file, indent=2)
    with open(SCRIPT_DATA / "creds.json", "w+") as creds_file:
        json.dump(USERS, creds_file, indent=2)


if __name__ == "__main__":
    main()
