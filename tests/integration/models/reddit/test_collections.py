"""Test classes from collections.py."""

import pytest

from asyncpraw.exceptions import ClientException, RedditAPIException
from asyncpraw.models import Submission

from ... import IntegrationTest


class TestCollection(IntegrationTest):
    NONEMPTY_REAL_UUID = "3aa31024-711b-46b2-9514-3fd50619f6e8"

    async def test_bad_fetch(self, reddit):
        uuid = "A" * 36
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        with pytest.raises(ClientException):
            await subreddit.collections(uuid)

    async def test_follow(self, reddit):
        reddit.read_only = False
        uuid = self.NONEMPTY_REAL_UUID
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        collection = await subreddit.collections(uuid)
        await collection.follow()

    async def test_init(self, reddit):
        uuid = self.NONEMPTY_REAL_UUID
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        collection1 = await subreddit.collections(uuid)
        collection2 = await subreddit.collections(permalink=collection1.permalink)
        assert collection1 == collection2

    async def test_iter(self, reddit):
        uuid = self.NONEMPTY_REAL_UUID
        found_some = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        collection = await subreddit.collections(uuid)
        for post in collection:
            assert isinstance(post, Submission)
            found_some = True
        assert found_some

    async def test_subreddit(self, reddit):
        uuid = self.NONEMPTY_REAL_UUID
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        collection = await subreddit.collections(uuid)
        assert str(await collection.subreddit()) in collection.permalink

    async def test_unfollow(self, reddit):
        reddit.read_only = False
        uuid = self.NONEMPTY_REAL_UUID
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        collection = await subreddit.collections(uuid)
        await collection.unfollow()


class TestCollectionModeration(IntegrationTest):
    NONEMPTY_REAL_UUID = "3aa31024-711b-46b2-9514-3fd50619f6e8"
    UPDATE_LAYOUT_UUID = "3aa31024-711b-46b2-9514-3fd50619f6e8"

    async def test_add_post(self, reddit):
        reddit.read_only = False
        uuid = self.NONEMPTY_REAL_UUID
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        collection = await subreddit.collections(uuid)
        posts = [await subreddit.submit(f"Post #{i}", selftext="") for i in range(4)]
        for post in posts:
            await post._fetch()
        # Testing different types for _post_fullname
        await collection.mod.add_post(posts[0])  # Subreddit object
        await collection.mod.add_post(posts[1].fullname)  # fullname
        await collection.mod.add_post(f"https://reddit.com{posts[2].permalink}")
        await collection.mod.add_post(posts[3].id)  # id

        posts.append(await subreddit.submit("Post #4", collection_id=uuid, selftext=""))

        with pytest.raises(TypeError):
            await collection.mod.add_post(12345)

        await collection._fetch()

        collection_set = set(collection)
        for post in posts:
            assert post in collection_set

    async def test_delete(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit, fetch=True)
        collection = await subreddit.collections.mod.create(title="Title", description="")
        await collection.mod.delete()

    async def test_remove_post(self, reddit):
        reddit.read_only = False
        uuid = self.NONEMPTY_REAL_UUID
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        post = await subreddit.submit("The title", collection_id=uuid, selftext="")
        collection = await subreddit.collections(uuid)
        await collection.mod.remove_post(post)

    async def test_reorder(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        collection = await subreddit.collections(self.NONEMPTY_REAL_UUID)
        original_order = collection.link_ids
        new_order = (
            collection.link_ids[len(collection.link_ids) // 2 :] + collection.link_ids[: len(collection.link_ids) // 2]
        )
        assert len(original_order) == len(new_order)
        assert original_order != new_order
        await collection.mod.reorder(new_order)
        await collection._fetch()
        assert collection.link_ids == new_order

    async def test_update_description(self, reddit):
        reddit.read_only = False
        uuid = self.NONEMPTY_REAL_UUID
        new_description = "b" * 250
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        collection = await subreddit.collections(uuid)
        await collection.mod.update_description(new_description)
        assert new_description == collection.description

    async def test_update_display_layout__empty_string(self, reddit):
        reddit.read_only = False
        uuid = self.UPDATE_LAYOUT_UUID
        empty_string = ""
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        collection = await subreddit.collections(uuid, fetch=False)
        await collection.mod.update_display_layout(empty_string)
        await collection.load()
        assert empty_string != collection.display_layout
        assert collection.display_layout is None

    async def test_update_display_layout__gallery(self, reddit):
        reddit.read_only = False
        uuid = self.UPDATE_LAYOUT_UUID
        gallery_layout = "GALLERY"
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        collection = await subreddit.collections(uuid, fetch=False)
        await collection.mod.update_display_layout(gallery_layout)
        await collection.load()
        assert gallery_layout == collection.display_layout

    async def test_update_display_layout__invalid_layout(self, reddit):
        reddit.read_only = False
        uuid = self.UPDATE_LAYOUT_UUID
        invalid_layout = "colossal atom cake"
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        collection = await subreddit.collections(uuid, fetch=False)
        with pytest.raises(RedditAPIException):
            await collection.mod.update_display_layout(invalid_layout)
        await collection.load()
        assert collection.display_layout is None

    async def test_update_display_layout__lowercase(self, reddit):
        reddit.read_only = False
        uuid = self.UPDATE_LAYOUT_UUID
        lowercase_gallery_layout = "gallery"
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        collection = await subreddit.collections(uuid, fetch=False)
        with pytest.raises(RedditAPIException):
            await collection.mod.update_display_layout(lowercase_gallery_layout)
        await collection.load()
        assert collection.display_layout is None

    async def test_update_display_layout__none(self, reddit):
        reddit.read_only = False
        uuid = self.UPDATE_LAYOUT_UUID
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        collection = await subreddit.collections(uuid, fetch=False)
        await collection.mod.update_display_layout(None)
        await collection.load()
        assert collection.display_layout is None

    async def test_update_display_layout__timeline(self, reddit):
        reddit.read_only = False
        uuid = self.UPDATE_LAYOUT_UUID
        timeline_layout = "TIMELINE"
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        collection = await subreddit.collections(uuid, fetch=False)
        await collection.mod.update_display_layout(timeline_layout)
        await collection.load()
        assert timeline_layout == collection.display_layout

    async def test_update_title(self, reddit):
        reddit.read_only = False
        uuid = self.NONEMPTY_REAL_UUID
        new_title = "a" * 100
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        collection = await subreddit.collections(uuid)
        await collection.mod.update_title(new_title)
        assert new_title == collection.title


class TestSubredditCollections(IntegrationTest):
    async def test_call(self, reddit):
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        collection = next(iter(await self.async_list(subreddit.collections)))
        test_collection = await subreddit.collections(collection.collection_id)
        assert collection == test_collection
        test_collection = await subreddit.collections(permalink=collection.permalink)
        assert collection == test_collection

    async def test_iter(self, reddit):
        found_any = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        async for collection in subreddit.collections:
            assert collection.permalink
            assert collection.title is not None
            assert collection.description is not None
            found_any = True
        assert found_any


class TestSubredditCollectionsModeration(IntegrationTest):
    async def test_create(self, reddit):
        title = "The title!"
        description = "The description."
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        collection = await subreddit.collections.mod.create(title=title, description=description)
        assert collection.title == title
        assert collection.description == description
        assert len(collection) == 0

    async def test_create__empty_layout(self, reddit):
        title = "The title!"
        description = "The description."
        layout = ""
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        collection = await subreddit.collections.mod.create(title=title, description=description, display_layout=layout)
        assert collection.title == title
        assert collection.description == description
        assert collection.display_layout is None
        assert len(collection) == 0

    async def test_create__gallery_layout(self, reddit):
        title = "The title!"
        description = "The description."
        layout = "GALLERY"
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        collection = await subreddit.collections.mod.create(title=title, description=description, display_layout=layout)
        assert collection.title == title
        assert collection.description == description
        assert collection.display_layout == layout
        assert len(collection) == 0

    async def test_create__invalid_layout(self, reddit):
        title = "The title!"
        description = "The description."
        layout = "milk before cereal"
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        with pytest.raises(RedditAPIException):
            await subreddit.collections.mod.create(title=title, description=description, display_layout=layout)

    async def test_create__lowercase_layout(self, reddit):
        title = "The title!"
        description = "The description."
        layout = "gallery"
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        with pytest.raises(RedditAPIException):
            await subreddit.collections.mod.create(title=title, description=description, display_layout=layout)

    async def test_create__none_layout(self, reddit):
        title = "The title!"
        description = "The description."
        layout = None
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        collection = await subreddit.collections.mod.create(title=title, description=description, display_layout=layout)
        assert collection.title == title
        assert collection.description == description
        assert collection.display_layout is None
        assert len(collection) == 0

    async def test_create__timeline_layout(self, reddit):
        title = "The title!"
        description = "The description."
        layout = "TIMELINE"
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        collection = await subreddit.collections.mod.create(title=title, description=description, display_layout=layout)
        assert collection.title == title
        assert collection.description == description
        assert collection.display_layout == layout
        assert len(collection) == 0
