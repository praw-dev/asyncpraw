"""Test asyncpraw.models.reddit.announcement."""

from asyncpraw.models import Announcement
from asyncpraw.models.listing.generator import ListingGenerator

from ... import IntegrationTest


class TestAnnouncement(IntegrationTest):
    async def test_hide(self, reddit):
        reddit.read_only = False
        announcement = await anext(reddit.announcements())
        await announcement.hide()

    async def test_mark_read(self, reddit):
        reddit.read_only = False
        announcement = await anext(reddit.announcements())
        await announcement.mark_read()
        # Re-fetch the same announcement to confirm read_at is now set.
        refreshed = None
        async for a in reddit.announcements():
            if a.id == announcement.id:
                refreshed = a
                break
        assert refreshed is not None
        assert refreshed.read_at is not None


class TestAnnouncementHelper(IntegrationTest):
    async def test_call(self, reddit):
        reddit.read_only = False
        generator = reddit.announcements()
        assert isinstance(generator, ListingGenerator)
        count = 0
        async for announcement in generator:
            assert isinstance(announcement, Announcement)
            assert announcement.id.startswith("ann_")
            assert announcement.fullname == announcement.id
            count += 1
        assert count > 0

    async def test_call__pagination(self, reddit):
        reddit.read_only = False
        # Drive pagination by requesting more than fits in a single response.
        announcements = [a async for a in reddit.announcements(limit=4, request_limit=2)]
        assert len(announcements) > 2
        # Ensure no duplicates across pages.
        ids = [a.id for a in announcements]
        assert len(set(ids)) == len(ids)

    async def test_call__with_limit(self, reddit):
        reddit.read_only = False
        announcements = [a async for a in reddit.announcements(limit=5)]
        assert len(announcements) == 5
        assert all(isinstance(a, Announcement) for a in announcements)

    async def test_hide(self, reddit):
        reddit.read_only = False
        announcements = [a async for a in reddit.announcements(limit=2)]
        await reddit.announcements.hide(announcements)

    async def test_mark_all_read(self, reddit):
        reddit.read_only = False
        await reddit.announcements.mark_all_read()
        async for announcement in reddit.announcements(limit=10):
            assert announcement.read_at is not None

    async def test_mark_read(self, reddit):
        reddit.read_only = False
        unread = [a async for a in reddit.announcements(limit=25) if a.read_at is None]
        await reddit.announcements.mark_read(unread)
        unread_ids = {a.id for a in unread}
        async for announcement in reddit.announcements(limit=25):
            if announcement.id in unread_ids:
                assert announcement.read_at is not None
