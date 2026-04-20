"""
Control-M skill implementation with multi-region support
Provides Control-M job management capabilities across multiple regions
"""
import logging
from typing import Any, Dict, Optional

import httpx
from pydantic import BaseModel, Field

from app.config.settings import ControlMRegionSettings, get_settings
from app.skills.base import BaseSkill, SkillExecutionError, SkillOutput
from app.skills.controlm_region_router import ControlMRegionRouter

logger = logging.getLogger(__name__)


class ControlMJobParams(BaseModel):
    """Control-M skill parameters with region support"""
    action: str = Field(..., description="Action type: run | status | hold | free | delete")
    job_name: Optional[str] = Field(None, description="Job name")
    folder_name: Optional[str] = Field(None, description="Folder name")
    server_name: Optional[str] = Field(None, description="Control-M Server name")
    run_id: Optional[str] = Field(None, description="Run ID (used when querying status)")
    region: Optional[str] = Field(
        None,
        description="Target region (e.g., 'us-east', 'eu-west'). Auto-detected if not specified."
    )


class ControlMSkill(BaseSkill):
    """
    Control-M job scheduling skill with multi-region support
    Supports triggering jobs, checking status, holding, and releasing jobs across multiple regions
    
    Region Detection Strategy:
    1. Explicit region parameter in request
    2. User query analysis (LLM-based)
    3. Job/folder naming conventions
    4. Default region fallback
    """

    name = "controlm_job"
    description = "Manage Control-M scheduling jobs across multiple regions: trigger execution, query status, hold/release jobs"
    
    # Define which actions require change management approval (ITIL terminology)
    CHG_REQUIRE_ACTIONS = {"run", "hold", "free", "delete"}

    def __init__(self):
        super().__init__()
        self._settings = get_settings().controlm
        self._region_router = ControlMRegionRouter(self._settings)
        
        # Token cache per region
        self._region_tokens: Dict[str, str] = {}
        
        logger.info(
            f"[ControlMSkill] Initialized with {len(self._settings.regions)} regions. "
            f"Region detection: {'enabled' if self._settings.enable_region_detection else 'disabled'}"
        )

    async def _get_auth_token(self, region_config: ControlMRegionSettings) -> str:
        """Fetch Control-M authentication token for specific region"""
        region_name = region_config.name
        
        if region_name in self._region_tokens:
            return self._region_tokens[region_name]
        
        async with httpx.AsyncClient(verify=region_config.verify_ssl) as client:
            resp = await client.post(
                f"{region_config.base_url}/session/login",
                json={
                    "username": region_config.username,
                    "password": region_config.password,
                },
                timeout=region_config.request_timeout,
            )
            resp.raise_for_status()
            token = resp.json().get("token", "")
            self._region_tokens[region_name] = token
            return token

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
        """Execute a Control-M operation with region detection"""
        
        try:
            job_params = ControlMJobParams(**params)
        except Exception as e:
            return SkillOutput(success=False, error_message=f"Parameter validation failed: {e}")

        action = job_params.action.lower()
        
        # Detect target region
        try:
            detected_region = await self._detect_target_region(job_params, params.get("user_query", ""))
            region_config = self._region_router.get_region_config(detected_region)
            
            if not region_config:
                return SkillOutput(
                    success=False,
                    error_message=f"Region '{detected_region}' is not configured"
                )
            
            logger.info(
                f"[ControlMSkill] Executing action={action} in region={detected_region} "
                f"(confidence={detected_region.confidence:.2f})"
            )
            
        except ValueError as e:
            return SkillOutput(success=False, error_message=str(e))
        except Exception as e:
            logger.error(f"[ControlMSkill] Region detection failed: {e}", exc_info=True)
            return SkillOutput(
                success=False,
                error_message=f"Failed to detect target region: {e}"
            )

        try:
            token = await self._get_auth_token(region_config)
            headers = {"x-api-key": token, "Content-Type": "application/json"}

            async with httpx.AsyncClient(verify=region_config.verify_ssl) as client:
                if action == "run":
                    return await self._run_job(client, headers, job_params, region_config)
                elif action == "status":
                    return await self._get_status(client, headers, job_params, region_config)
                elif action in ("hold", "free"):
                    return await self._hold_or_free(client, headers, job_params, action, region_config)
                else:
                    return SkillOutput(success=False, error_message=f"Unsupported operation: {action}")

        except httpx.TimeoutException:
            raise SkillExecutionError(
                self.name,
                f"Control-M API request timeout (region: {region_config.name})",
                retriable=True
            )
        except httpx.HTTPStatusError as e:
            raise SkillExecutionError(
                self.name,
                f"Control-M API error in region {region_config.name}: {e.response.status_code}",
                retriable=False
            )
        except Exception as e:
            raise SkillExecutionError(
                self.name,
                f"Unknown error in region {region_config.name}: {e}",
                retriable=True
            )
    
    async def _detect_target_region(
        self,
        job_params: ControlMJobParams,
        user_query: str
    ) -> str:
        """
        Detect target region using multiple strategies
        
        Priority:
        1. Explicit region parameter
        2. Region router detection (LLM + naming + keywords)
        3. Default region fallback
        """
        
        # Strategy 1: Use explicit region parameter if provided
        if job_params.region:
            logger.info(f"[ControlMSkill] Using explicit region parameter: {job_params.region}")
            return job_params.region.lower()
        
        # Strategy 2: Use region router for intelligent detection
        detection_result = await self._region_router.detect_region(
            user_query=user_query,
            job_name=job_params.job_name,
            folder_name=job_params.folder_name
        )
        
        logger.info(
            f"[ControlMSkill] Region detected: {detection_result.detected_region} "
            f"(confidence={detection_result.confidence:.2f}, "
            f"reasoning={detection_result.reasoning})"
        )
        
        return detection_result.detected_region

    async def _run_job(
        self,
        client,
        headers,
        params: ControlMJobParams,
        region_config: ControlMRegionSettings
    ) -> SkillOutput:
        """Trigger job execution in specific region"""
        payload = {
            "jobs": {
                params.job_name: {
                    "host": params.server_name or "default",
                    "folder": params.folder_name or "",
                }
            }
        }
        resp = await client.post(
            f"{region_config.base_url}/run/order",
            headers=headers,
            json=payload,
            timeout=region_config.request_timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return SkillOutput(
            success=True,
            data={
                "run_id": data.get("runId"),
                "message": f"Job '{params.job_name}' has been successfully triggered in region '{region_config.name}'",
                "region": region_config.name,
            },
        )

    async def _get_status(
        self,
        client,
        headers,
        params: ControlMJobParams,
        region_config: ControlMRegionSettings
    ) -> SkillOutput:
        """Query job status in specific region"""
        query_params = {"limit": 50}
        if params.run_id:
            query_params["runId"] = params.run_id
        elif params.job_name:
            query_params["jobname"] = params.job_name

        resp = await client.get(
            f"{region_config.base_url}/run/status",
            headers=headers,
            params=query_params,
            timeout=region_config.request_timeout,
        )
        resp.raise_for_status()
        statuses = resp.json().get("statuses", [])
        return SkillOutput(
            success=True,
            data={
                "statuses": statuses,
                "count": len(statuses),
                "region": region_config.name
            }
        )

    async def _hold_or_free(
        self,
        client,
        headers,
        params: ControlMJobParams,
        action: str,
        region_config: ControlMRegionSettings
    ) -> SkillOutput:
        """Hold or release a job in specific region"""
        endpoint = f"{region_config.base_url}/run/{action}"
        resp = await client.post(
            endpoint,
            headers=headers,
            json={"runId": params.run_id},
            timeout=region_config.request_timeout,
        )
        resp.raise_for_status()
        return SkillOutput(
            success=True,
            data={
                "message": f"Job has been {'held' if action == 'hold' else 'released'} in region '{region_config.name}'",
                "region": region_config.name
            },
        )

    def get_tool_schema(self) -> Dict[str, Any]:
        # Build region enum from configured regions
        region_enum = list(self._settings.regions.keys()) if self._settings.has_multiple_regions() else []
        
        schema = {
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
                        "run_id": {"type": "string", "description": "Run ID for status query or hold/free operations"},
                    },
                    "required": ["action"],
                },
            },
        }
        
        # Add region parameter if multiple regions are configured
        if region_enum:
            schema["function"]["parameters"]["properties"]["region"] = {
                "type": "string",
                "enum": region_enum,
                "description": f"Target Control-M region. Auto-detected from context if not specified. Available: {', '.join(region_enum)}"
            }
        
        return schema
    
    def get_region_info(self) -> Dict[str, Any]:
        """Get information about available regions (for debugging/monitoring)"""
        return {
            "regions": self._region_router.list_available_regions(),
            "default_region": self._settings.default_region,
            "region_detection_enabled": self._settings.enable_region_detection,
            "total_regions": len(self._settings.regions)
        }
