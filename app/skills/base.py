"""
Base skill module
All skills must inherit from BaseSkill and implement the execute method.
Skills are integrated as plugins and registered through a central SkillRegistry.
"""
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class SkillInput(BaseModel):
    """Base class for skill input"""
    pass


class SkillOutput(BaseModel):
    """Base class for skill output"""
    success: bool = True
    data: Optional[Any] = None
    error_message: Optional[str] = None
    executed_at: datetime = datetime.utcnow()


class SkillExecutionError(Exception):
    """Skill execution exception"""
    def __init__(self, skill_name: str, message: str, retriable: bool = True):
        self.skill_name = skill_name
        self.retriable = retriable
        super().__init__(f"[{skill_name}] {message}")


class BaseSkill(ABC):
    """
    Base skill
    
    All business skills must inherit from this class and provide:
    - a unified execution entrypoint (execute)
    - automatic exception handling and retries
    - standard logging instrumentation
    """

# subclasses must define these attributes
    name: str = ""                    # unique skill identifier
    description: str = ""             # skill description (used for LLM routing decisions)
    require_human_approval: bool = False   # whether human approval is required

    def __init__(self):
        if not self.name:
            raise ValueError(f"{self.__class__.__name__} must define `name`")
        self.logger = logging.getLogger(f"skill.{self.name}")

    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> SkillOutput:
        """
        Execute the main skill logic (must be implemented by subclasses)
        
        Args:
            params: Execution parameters dictionary
            
        Returns:
            SkillOutput execution result
        """
        ...

    async def safe_execute(
        self,
        params: Dict[str, Any],
        max_retries: int = 3,
    ) -> SkillOutput:
        """
        Safe execution entry point with retry mechanism
        
        Args:
            params: Execution parameters
            max_retries: Maximum number of retries
            
        Returns:
            SkillOutput execution result
        """
        last_error: Optional[Exception] = None
        for attempt in range(1, max_retries + 1):
            try:
                self.logger.info(f"Executing skill '{self.name}', attempt {attempt}/{max_retries}")
                result = await self.execute(params)
                self.logger.info(f"Skill '{self.name}' succeeded on attempt {attempt}")
                return result
            except SkillExecutionError as e:
                last_error = e
                if not e.retriable:
                    self.logger.error(f"Skill '{self.name}' non-retriable error: {e}")
                    break
                self.logger.warning(f"Skill '{self.name}' attempt {attempt} failed: {e}, retrying...")
            except Exception as e:
                last_error = e
                self.logger.warning(f"Skill '{self.name}' attempt {attempt} unexpected error: {e}", exc_info=True)

        error_msg = str(last_error) if last_error else "Unknown error"
        return SkillOutput(success=False, error_message=error_msg)

    def get_tool_schema(self) -> Dict[str, Any]:
        """
        Return the OpenAI function-calling tool schema
        Subclasses may override to customize parameter descriptions
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        }


class SkillRegistry:
    """
    Skill registry (singleton)
    Responsible for registering, locating, and invoking all registered skills
    """

    _instance: Optional["SkillRegistry"] = None
    _skills: Dict[str, BaseSkill] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, skill: BaseSkill) -> None:
        """Register a skill instance"""
        if skill.name in self._skills:
            logger.warning(f"Skill '{skill.name}' is being overwritten in registry")
        self._skills[skill.name] = skill
        logger.info(f"Skill registered: {skill.name}")

    def register_class(self, skill_cls: Type[BaseSkill]) -> None:
        """Register a skill class (auto-instantiate)"""
        self.register(skill_cls())

    def get(self, skill_name: str) -> Optional[BaseSkill]:
        """Get a skill by name"""
        return self._skills.get(skill_name)

    def get_all_skills(self) -> Dict[str, BaseSkill]:
        """Get all registered skills"""
        return dict(self._skills)

    def get_tool_schemas(self) -> list:
        """Get tool schemas for all skills (for LLM function calling)"""
        return [skill.get_tool_schema() for skill in self._skills.values()]

    def list_skill_names(self) -> list:
        return list(self._skills.keys())

    def clear(self) -> None:
        """Clear all registered skills (useful for testing)"""
        self._skills.clear()
        logger.info("Skill registry cleared")


# global registry
skill_registry = SkillRegistry()
