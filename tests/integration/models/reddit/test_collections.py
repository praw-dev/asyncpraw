"""Test classes from collections.py."""

import pytest
from asynctest import mock

from asyncpraw.exceptions import ClientException
from asyncpraw.models import Submission

from ... import IntegrationTest


class TestCollection(IntegrationTest):
    NONEMPTY_REAL_UUID = "3aa31024-711b-46b2-9514-3fd50619f6e8"

    async def test_bad_fetch(self):
        uuid = "A" * 36
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            with pytest.raises(ClientException):
                await subreddit.collections(uuid)

    async def test_init(self):
        uuid = self.NONEMPTY_REAL_UUID
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            collection1 = await subreddit.collections(uuid)
            collection2 = await subreddit.collections(permalink=collection1.permalink)
            assert collection1 == collection2

    async def test_iter(self):
        uuid = self.NONEMPTY_REAL_UUID
        found_some = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            collection = await subreddit.collections(uuid)
            for post in collection:
                assert isinstance(post, Submission)
                found_some = True
        assert found_some

    async def test_follow(self):
        self.reddit.read_only = False
        uuid = self.NONEMPTY_REAL_UUID
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            collection = await subreddit.collections(uuid)
            await collection.follow()

    async def test_subreddit(self):
        uuid = self.NONEMPTY_REAL_UUID
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            collection = await subreddit.collections(uuid)
            assert str(await collection.subreddit()) in collection.permalink

    async def test_unfollow(self):
        self.reddit.read_only = False
        uuid = self.NONEMPTY_REAL_UUID
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            collection = await subreddit.collections(uuid)
            await collection.unfollow()


class TestCollectionModeration(IntegrationTest):
    NONEMPTY_REAL_UUID = "3aa31024-711b-46b2-9514-3fd50619f6e8"

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_add_post(self, _):
        self.reddit.read_only = False
        uuid = self.NONEMPTY_REAL_UUID
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            collection = await subreddit.collections(uuid)
            posts = [
                await subreddit.submit(f"Post #{i}", selftext="") for i in range(4)
            ]
            for post in posts:
                await post._fetch()
            # Testing different types for _post_fullname
            await collection.mod.add_post(posts[0])  # Subreddit object
            await collection.mod.add_post(posts[1].fullname)  # fullname
            await collection.mod.add_post(f"https://reddit.com{posts[2].permalink}")
            await collection.mod.add_post(posts[3].id)  # id

            posts.append(
                await subreddit.submit("Post #4", selftext="", collection_id=uuid)
            )

            with pytest.raises(TypeError):
                await collection.mod.add_post(12345)

            await collection._fetch()

            collection_set = set(collection)
            for post in posts:
                assert post in collection_set

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_delete(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(
                pytest.placeholders.test_subreddit, fetch=True
            )
            collection = await subreddit.collections.mod.create("Title", "")
            await collection.mod.delete()

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_remove_post(self, _):
        self.reddit.read_only = False
        uuid = self.NONEMPTY_REAL_UUID
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            post = await subreddit.submit("The title", selftext="", collection_id=uuid)
            collection = await subreddit.collections(uuid)
            await collection.mod.remove_post(post)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_reorder(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            collection = await subreddit.collections(self.NONEMPTY_REAL_UUID)
            original_order = collection.link_ids
            new_order = (
                collection.link_ids[len(collection.link_ids) // 2 :]
                + collection.link_ids[: len(collection.link_ids) // 2]
            )
            assert len(original_order) == len(new_order)
            assert original_order != new_order
            await collection.mod.reorder(new_order)
            await collection._fetch()
            assert collection.link_ids == new_order

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update_description(self, _):
        self.reddit.read_only = False
        uuid = self.NONEMPTY_REAL_UUID
        new_description = "b" * 250
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            collection = await subreddit.collections(uuid)
            await collection.mod.update_description(new_description)
            assert new_description == collection.description

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update_title(self, _):
        self.reddit.read_only = False
        uuid = self.NONEMPTY_REAL_UUID
        new_title = "a" * 100
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            collection = await subreddit.collections(uuid)
            await collection.mod.update_title(new_title)
            assert new_title == collection.title


class TestSubredditCollections(IntegrationTest):
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_call(self, _):
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            collection = await self.async_next(subreddit.collections)
            test_collection = await subreddit.collections(collection.collection_id)
            assert collection == test_collection
            test_collection = await subreddit.collections(
                permalink=collection.permalink
            )
            assert collection == test_collection

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_iter(self, _):
        with self.use_cassette():
            found_any = False
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            async for collection in subreddit.collections:
                assert collection.permalink
                assert collection.title is not None
                assert collection.description is not None
                found_any = True
            assert found_any


class TestSubredditCollectionsModeration(IntegrationTest):
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_create(self, _):
        title = "The title!"
        description = "The description."
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            collection = await subreddit.collections.mod.create(title, description)
            assert collection.title == title
            assert collection.description == description
            assert len(collection) == 0
