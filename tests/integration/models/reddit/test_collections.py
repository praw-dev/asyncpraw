"""Test classes from collections.py."""

import sys

import pytest

if sys.version_info < (3, 8):
    from asynctest import mock
else:
    from unittest import mock

from asyncpraw.exceptions import ClientException, RedditAPIException
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
    UPDATE_LAYOUT_UUID = "3aa31024-711b-46b2-9514-3fd50619f6e8"

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
                await subreddit.submit("Post #4", collection_id=uuid, selftext="")
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
            collection = await subreddit.collections.mod.create(
                title="Title", description=""
            )
            await collection.mod.delete()

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_remove_post(self, _):
        self.reddit.read_only = False
        uuid = self.NONEMPTY_REAL_UUID
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            post = await subreddit.submit("The title", collection_id=uuid, selftext="")
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
    async def test_update_display_layout__empty_string(self, _):
        self.reddit.read_only = False
        uuid = self.UPDATE_LAYOUT_UUID
        empty_string = ""
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            collection = await subreddit.collections(uuid, fetch=False)
            await collection.mod.update_display_layout(empty_string)
            await collection.load()
            assert empty_string != collection.display_layout
            assert collection.display_layout is None

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update_display_layout__gallery(self, _):
        self.reddit.read_only = False
        uuid = self.UPDATE_LAYOUT_UUID
        gallery_layout = "GALLERY"
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            collection = await subreddit.collections(uuid, fetch=False)
            await collection.mod.update_display_layout(gallery_layout)
            await collection.load()
            assert gallery_layout == collection.display_layout

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update_display_layout__invalid_layout(self, _):
        self.reddit.read_only = False
        uuid = self.UPDATE_LAYOUT_UUID
        invalid_layout = "colossal atom cake"
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            collection = await subreddit.collections(uuid, fetch=False)
            with pytest.raises(RedditAPIException):
                await collection.mod.update_display_layout(invalid_layout)
            await collection.load()
            assert collection.display_layout is None

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update_display_layout__lowercase(self, _):
        self.reddit.read_only = False
        uuid = self.UPDATE_LAYOUT_UUID
        lowercase_gallery_layout = "gallery"
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            collection = await subreddit.collections(uuid, fetch=False)
            with pytest.raises(RedditAPIException):
                await collection.mod.update_display_layout(lowercase_gallery_layout)
            await collection.load()
            assert collection.display_layout is None

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update_display_layout__none(self, _):
        self.reddit.read_only = False
        uuid = self.UPDATE_LAYOUT_UUID
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            collection = await subreddit.collections(uuid, fetch=False)
            await collection.mod.update_display_layout(None)
            await collection.load()
            assert collection.display_layout is None

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update_display_layout__timeline(self, _):
        self.reddit.read_only = False
        uuid = self.UPDATE_LAYOUT_UUID
        timeline_layout = "TIMELINE"
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            collection = await subreddit.collections(uuid, fetch=False)
            await collection.mod.update_display_layout(timeline_layout)
            await collection.load()
            assert timeline_layout == collection.display_layout

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
            collection = next(iter(await self.async_list(subreddit.collections)))
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
            collection = await subreddit.collections.mod.create(
                title=title, description=description
            )
            assert collection.title == title
            assert collection.description == description
            assert len(collection) == 0

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_create__empty_layout(self, _):
        title = "The title!"
        description = "The description."
        layout = ""
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            collection = await subreddit.collections.mod.create(
                title=title, description=description, display_layout=layout
            )
            assert collection.title == title
            assert collection.description == description
            assert collection.display_layout is None
            assert len(collection) == 0

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_create__gallery_layout(self, _):
        title = "The title!"
        description = "The description."
        layout = "GALLERY"
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            collection = await subreddit.collections.mod.create(
                title=title, description=description, display_layout=layout
            )
            assert collection.title == title
            assert collection.description == description
            assert collection.display_layout == layout
            assert len(collection) == 0

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_create__invalid_layout(self, _):
        title = "The title!"
        description = "The description."
        layout = "milk before cereal"
        self.reddit.read_only = False
        with self.use_cassette():
            with pytest.raises(RedditAPIException):
                subreddit = await self.reddit.subreddit(
                    pytest.placeholders.test_subreddit
                )
                await subreddit.collections.mod.create(
                    title=title, description=description, display_layout=layout
                )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_create__lowercase_layout(self, _):
        title = "The title!"
        description = "The description."
        layout = "gallery"
        self.reddit.read_only = False
        with self.use_cassette():
            with pytest.raises(RedditAPIException):
                subreddit = await self.reddit.subreddit(
                    pytest.placeholders.test_subreddit
                )
                await subreddit.collections.mod.create(
                    title=title, description=description, display_layout=layout
                )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_create__none_layout(self, _):
        title = "The title!"
        description = "The description."
        layout = None
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            collection = await subreddit.collections.mod.create(
                title=title, description=description, display_layout=layout
            )
            assert collection.title == title
            assert collection.description == description
            assert collection.display_layout is None
            assert len(collection) == 0

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_create__timeline_layout(self, _):
        title = "The title!"
        description = "The description."
        layout = "TIMELINE"
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            collection = await subreddit.collections.mod.create(
                title=title, description=description, display_layout=layout
            )
            assert collection.title == title
            assert collection.description == description
            assert collection.display_layout == layout
            assert len(collection) == 0
