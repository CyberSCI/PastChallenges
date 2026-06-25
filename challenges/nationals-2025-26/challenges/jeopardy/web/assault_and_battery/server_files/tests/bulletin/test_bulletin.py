from bulletin.models import Bulletin


def test_bulletin_create(db):
    title = "General"
    bulletin = Bulletin.objects.create(title=title)
    assert bulletin.updated_at >= bulletin.updated_at
    assert bulletin.title == title
    assert bulletin.pk != 0

    assert Bulletin.objects.get(pk=bulletin.pk) is not None
