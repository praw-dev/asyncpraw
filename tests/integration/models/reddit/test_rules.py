import pytest

from asyncpraw.exceptions import ClientException, RedditAPIException
from asyncpraw.models import Rule

from ... import IntegrationTest


class TestRule(IntegrationTest):
    async def test_add_rule(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        rule = await subreddit.rules.mod.add(
            short_name="PRAW Test",
            kind="all",
            description="Test by Async PRAW",
            violation_reason="PTest",
        )
        assert rule.short_name == "PRAW Test"
        assert rule.kind == "all"
        assert rule.description == "Test by Async PRAW"
        assert rule.violation_reason == "PTest"

    async def test_add_rule_without_violation_reason(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        rule = await subreddit.rules.mod.add(short_name="PRAW Test 2", kind="comment")
        assert rule.short_name == "PRAW Test 2"
        assert rule.kind == "comment"
        assert rule.description == ""
        assert rule.violation_reason == "PRAW Test 2"

    @pytest.mark.filterwarnings("ignore", category=DeprecationWarning)
    async def test_aiter_call(self, reddit):
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        rules = await subreddit.rules()
        assert rules["rules"][0]["short_name"] == "Test post 12"

    async def test_aiter_rules(self, reddit):
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        async for rule in subreddit.rules:
            assert isinstance(rule, Rule)

    async def test_delete_rule(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        rules = await self.async_list(subreddit.rules)
        rule = rules[-1]
        await rule.mod.delete()
        assert len(await self.async_list(subreddit.rules)) == (len(rules) - 1)

    @pytest.mark.cassette_name("TestRule.test_aiter_rules")
    async def test_iter_rule_int(self, reddit):
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        rule = await subreddit.rules.get_rule(0)
        assert isinstance(rule, Rule)

    @pytest.mark.cassette_name("TestRule.test_aiter_rules")
    async def test_iter_rule_invalid(self, reddit):
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        with pytest.raises(ClientException) as excinfo:
            await subreddit.rules.get_rule("fake rule")
        assert (
            excinfo.value.args[0]
            == f"Subreddit {subreddit} does not have the rule fake rule"
        )

    @pytest.mark.cassette_name("TestRule.test_aiter_rules")
    async def test_iter_rule_negative_int(self, reddit):
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        rule = await subreddit.rules.get_rule(-1)
        assert isinstance(rule, Rule)

    @pytest.mark.cassette_name("TestRule.test_aiter_rules")
    async def test_iter_rule_slice(self, reddit):
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        rules = await subreddit.rules.get_rule(slice(-3, None))
        assert len(rules) == 3
        for rule in rules:
            assert isinstance(rule, Rule)

    @pytest.mark.cassette_name("TestRule.test_aiter_rules")
    async def test_iter_rule_string(self, reddit):
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        rule = await subreddit.rules.get_rule("PRAW Test")
        assert isinstance(rule, Rule)
        assert rule.kind

    async def test_reorder_rules(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        rule_list = await self.async_list(subreddit.rules)
        reordered = rule_list[2:3] + rule_list[0:2] + rule_list[3:]
        rule_info = {rule.short_name: rule for rule in rule_list}
        await subreddit.rules.mod.reorder(reordered)
        new_rules = await self.async_list(subreddit.rules)
        assert new_rules != rule_list
        for rule in new_rules:
            assert rule_info[rule.short_name] == rule

    async def test_reorder_rules_double(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        rule_list = await self.async_list(subreddit.rules)
        with pytest.raises(RedditAPIException):
            await subreddit.rules.mod.reorder(rule_list + rule_list[0:1])

    async def test_reorder_rules_empty(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        with pytest.raises(RedditAPIException):
            await subreddit.rules.mod.reorder([])

    async def test_reorder_rules_no_reorder(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        rule_list = await self.async_list(subreddit.rules)
        new_list = await subreddit.rules.mod.reorder(rule_list)
        assert new_list == rule_list

    async def test_reorder_rules_omit(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        rule_list = await self.async_list(subreddit.rules)
        with pytest.raises(RedditAPIException):
            await subreddit.rules.mod.reorder(rule_list[:-1])

    async def test_update_rule(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        rule_list = await self.async_list(subreddit.rules)
        rule = rule_list[0]
        rule2 = await rule.mod.update(
            description="Updated rule",
            kind="link",
            violation_reason="PUpdate",
        )
        assert rule.description != rule2.description
        assert rule2.description == "Updated rule"
        assert rule.kind != rule2.kind
        assert rule2.kind == "link"
        assert rule.violation_reason != rule2.violation_reason
        assert rule2.violation_reason == "PUpdate"

    async def test_update_rule_no_params(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        rule = await subreddit.rules.get_rule("Test Rule")
        rule2 = await rule.mod.update()
        for attr in (
            "created_utc",
            "description",
            "kind",
            "priority",
            "short_name",
            "subreddit",
            "violation_reason",
        ):
            assert getattr(rule, attr) == getattr(rule2, attr)

    async def test_update_rule_short_name(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        rule = await subreddit.rules.get_rule("Test Rule")
        rule2 = await rule.mod.update(
            short_name="PRAW Update",
            description="Updated rule",
            kind="comment",
            violation_reason="PUpdate",
        )
        assert rule != rule2
        assert rule2.short_name == "PRAW Update"
        assert rule.description != rule2.description
        assert rule2.description == "Updated rule"
        assert rule.kind != rule2.kind
        assert rule2.kind == "comment"
        assert rule.violation_reason != rule2.violation_reason
        assert rule2.violation_reason == "PUpdate"
        async for new_rule in subreddit.rules:
            assert new_rule.short_name != rule.short_name
