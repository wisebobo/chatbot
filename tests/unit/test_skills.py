"""
Unit tests - skill registry
"""
import pytest
from app.skills.base import BaseSkill, SkillOutput, SkillRegistry


class MockSkill(BaseSkill):
    name = "mock_skill"
    description = "A mock skill for testing"

    async def execute(self, params):
        return SkillOutput(success=True, data={"result": "ok"})


def test_skill_registry_register():
    registry = SkillRegistry()
    registry.register(MockSkill())
    skill = registry.get("mock_skill")
    assert skill is not None
    assert skill.name == "mock_skill"


def test_skill_registry_list():
    registry = SkillRegistry()
    registry.register(MockSkill())
    names = registry.list_skill_names()
    assert "mock_skill" in names


@pytest.mark.asyncio
async def test_skill_safe_execute_success():
    skill = MockSkill()
    result = await skill.safe_execute({})
    assert result.success is True
    assert result.data == {"result": "ok"}
