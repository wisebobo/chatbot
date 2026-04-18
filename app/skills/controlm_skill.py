"""
Control-M skill implementation
Provides Control-M job management capabilities: query, trigger, monitor
"""
import logging
from typing import Any, Dict, Optional

import httpx
from pydantic import BaseModel, Field

from app.config.settings import get_settings
from app.skills.base import BaseSkill, SkillExecutionError, SkillOutput

logger = logging.getLogger(__name__)


class ControlMJobParams(BaseModel):
    """Control-M skill parameters"""
    action: str = Field(..., description="Action type: run | status | hold | free | delete")
    job_name: Optional[str] = Field(None, description="Job name")
    folder_name: Optional[str] = Field(None, description="Folder name")
    server_name: Optional[str] = Field(None, description="Control-M Server name")
    run_id: Optional[str] = Field(None, description="Run ID (used when querying status)")


class ControlMSkill(BaseSkill):
    """
    Control-M job scheduling skill
    Supports triggering jobs, checking status, holding, and releasing jobs
    """

    name = "controlm_job"
    description = "Manage Control-M scheduling jobs: trigger execution, query status, hold/release jobs"
    
    # Define which actions require change management approval (ITIL terminology)
    CHG_REQUIRE_ACTIONS = {"run", "hold", "free", "delete"}

    def __init__(self):
        super().__init__()
        self._settings = get_settings().controlm
        self._token: Optional[str] = None

    async def _get_auth_token(self) -> str:
        """Fetch Control-M authentication token"""
        if self._token:
            return self._token
        async with httpx.AsyncClient(verify=self._settings.verify_ssl) as client:
            resp = await client.post(
                f"{self._settings.base_url}/session/login",
                json={
                    "username": self._settings.username,
                    "password": self._settings.password,
                },
                timeout=self._settings.request_timeout,
            )
            resp.raise_for_status()
            self._token = resp.json().get("token", "")
            return self._token

    async def requires_approval_for(self, params: Dict[str, Any]) -> bool:
        """
        Dynamically determine if this specific execution requires human approval.
        
        Args:
            params: The execution parameters containing 'action' field
            
        Returns:
            True if the action is a write operation requiring approval, False otherwise
        """
        action = params.get("action", "").lower()
        needs_approval = action in self.CHG_REQUIRE_ACTIONS
        
        if needs_approval:
            logger.info(f"[controlm_skill] Action '{action}' identified as change-requiring operation - requires approval")
        else:
            logger.debug(f"[controlm_skill] Action '{action}' identified as read-only operation - no approval needed")
            
        return needs_approval

    async def execute(self, params: Dict[str, Any]) -> SkillOutput:
        """Execute a Control-M operation"""
        try:
            job_params = ControlMJobParams(**params)
        except Exception as e:
            return SkillOutput(success=False, error_message=f"Parameter validation failed: {e}")

        action = job_params.action.lower()
        self.logger.info(f"Control-M action={action}, job={job_params.job_name}")

        try:
            token = await self._get_auth_token()
            headers = {"x-api-key": token, "Content-Type": "application/json"}

            async with httpx.AsyncClient(verify=self._settings.verify_ssl) as client:
                if action == "run":
                    return await self._run_job(client, headers, job_params)
                elif action == "status":
                    return await self._get_status(client, headers, job_params)
                elif action in ("hold", "free"):
                    return await self._hold_or_free(client, headers, job_params, action)
                else:
                    return SkillOutput(success=False, error_message=f"Unsupported operation: {action}")

        except httpx.TimeoutException:
            raise SkillExecutionError(self.name, "Control-M API request timeout", retriable=True)
        except httpx.HTTPStatusError as e:
            raise SkillExecutionError(self.name, f"Control-M API error: {e.response.status_code}", retriable=False)
        except Exception as e:
            raise SkillExecutionError(self.name, f"Unknown error: {e}", retriable=True)

    async def _run_job(self, client, headers, params: ControlMJobParams) -> SkillOutput:
        """Trigger job execution"""
        payload = {
            "jobs": {
                params.job_name: {
                    "host": params.server_name or "default",
                    "folder": params.folder_name or "",
                }
            }
        }
        resp = await client.post(
            f"{self._settings.base_url}/run/order",
            headers=headers,
            json=payload,
            timeout=self._settings.request_timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return SkillOutput(
            success=True,
            data={
                "run_id": data.get("runId"),
                "message": f"Job '{params.job_name}' has been successfully triggered",
            },
        )

    async def _get_status(self, client, headers, params: ControlMJobParams) -> SkillOutput:
        """Query job status"""
        query_params = {"limit": 50}
        if params.run_id:
            query_params["runId"] = params.run_id
        elif params.job_name:
            query_params["jobname"] = params.job_name

        resp = await client.get(
            f"{self._settings.base_url}/run/status",
            headers=headers,
            params=query_params,
            timeout=self._settings.request_timeout,
        )
        resp.raise_for_status()
        statuses = resp.json().get("statuses", [])
        return SkillOutput(success=True, data={"statuses": statuses, "count": len(statuses)})

    async def _hold_or_free(self, client, headers, params: ControlMJobParams, action: str) -> SkillOutput:
        """Hold or release a job"""
        endpoint = f"{self._settings.base_url}/run/{action}"
        resp = await client.post(
            endpoint,
            headers=headers,
            json={"runId": params.run_id},
            timeout=self._settings.request_timeout,
        )
        resp.raise_for_status()
        return SkillOutput(
            success=True,
            data={"message": f"Job has been {'held' if action == 'hold' else 'released'}"},
        )

    def get_tool_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["run", "status", "hold", "free"],
                            "description": "Action to execute",
                        },
                        "job_name": {"type": "string", "description": "Control-M job name"},
                        "folder_name": {"type": "string", "description": "Folder where the job is located"},
                        "server_name": {"type": "string", "description": "Control-M Server name"},
                        "run_id": {"type": "string", "description": "Run ID"},
                    },
                    "required": ["action"],
                },
            },
        }
