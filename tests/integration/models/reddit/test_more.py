from asyncpraw.models import MoreComments

from ... import IntegrationTest


class TestMore(IntegrationTest):
    async def test_comments(self, reddit):
        data = {
            "children": [
                "cu5tt8h",
                "cu5v9yd",
                "cu5twf5",
                "cu5tkk4",
                "cu5tead",
                "cu5rxpy",
                "cu5oufs",
                "cu5tpek",
                "cu5pbdh",
            ],
            "count": 9,
            "id": "cu5tt8h",
            "name": "t1_cu5tt8h",
            "parent_id": "t3_3hahrw",
        }
        more = MoreComments(reddit, data)
        more.submission = await reddit.submission("3hahrw")
        assert len(await more.comments()) == 7

    async def test_comments__continue_thread_type(self, reddit):
        data = {
            "children": [],
            "count": 0,
            "id": "_",
            "name": "t1__",
            "parent_id": "t1_cu5v5h7",
        }
        more = MoreComments(reddit, data)
        more.submission = await reddit.submission("3hahrw")
        assert len(await more.comments()) == 1
