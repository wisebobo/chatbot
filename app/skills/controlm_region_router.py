"""
Control-M Region Router

Intelligently detects which Control-M region to use based on user intent,
job context, and LLM analysis.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

from app.config.settings import ControlMRegionSettings, ControlMSettings
from app.llm.adapter import get_llm_adapter

logger = logging.getLogger(__name__)


class RegionDetectionResult:
    """Result of region detection"""
    
    def __init__(
        self,
        detected_region: str,
        confidence: float,
        reasoning: str,
        fallback_used: bool = False
    ):
        self.detected_region = detected_region
        self.confidence = confidence
        self.reasoning = reasoning
        self.fallback_used = fallback_used
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "detected_region": self.detected_region,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "fallback_used": self.fallback_used
        }


class ControlMRegionRouter:
    """
    Routes Control-M requests to the appropriate region based on:
    1. Explicit region mention in user query
    2. Job naming conventions (e.g., job_us_, job_eu_)
    3. LLM-based intent analysis
    4. Default region fallback
    """
    
    def __init__(self, settings: ControlMSettings):
        self.settings = settings
        self.llm = get_llm_adapter() if settings.enable_region_detection else None
        
        # Build region keyword mapping for quick detection
        self.region_keywords = self._build_region_keywords()
        
        logger.info(
            f"[RegionRouter] Initialized with {len(settings.regions)} regions: "
            f"{', '.join(settings.regions.keys())}"
        )
    
    def _build_region_keywords(self) -> Dict[str, List[str]]:
        """Build keyword mapping for each region"""
        keywords = {}
        
        for region_name, region_config in self.settings.regions.items():
            # Use region name and description to build keywords
            kw_list = [region_name.lower()]
            
            # Add common aliases based on region name
            if 'us' in region_name or 'america' in region_name:
                kw_list.extend(['us', 'usa', 'america', 'american', 'north'])
            elif 'eu' in region_name or 'europe' in region_name:
                kw_list.extend(['eu', 'europe', 'european', 'west'])
            elif 'ap' in region_name or 'asia' in region_name or 'pacific' in region_name:
                kw_list.extend(['ap', 'asia', 'asian', 'pacific', 'east', 'china', 'japan'])
            
            # Add keywords from description
            if region_config.description:
                desc_lower = region_config.description.lower()
                for word in desc_lower.split():
                    if len(word) > 2:  # Skip short words
                        kw_list.append(word)
            
            keywords[region_name] = list(set(kw_list))  # Remove duplicates
        
        return keywords
    
    async def detect_region(
        self,
        user_query: str,
        job_name: Optional[str] = None,
        folder_name: Optional[str] = None
    ) -> RegionDetectionResult:
        """
        Detect which Control-M region to use
        
        Args:
            user_query: Original user query
            job_name: Control-M job name (may contain region hints)
            folder_name: Folder name (may contain region hints)
        
        Returns:
            RegionDetectionResult with detected region and confidence
        """
        
        # Strategy 1: Check for explicit region mentions in query
        explicit_region = self._detect_explicit_region(user_query)
        if explicit_region:
            logger.info(f"[RegionRouter] Explicit region detected: {explicit_region}")
            return RegionDetectionResult(
                detected_region=explicit_region,
                confidence=0.95,
                reasoning=f"Explicit region mention in query: '{explicit_region}'"
            )
        
        # Strategy 2: Check job/folder naming conventions
        naming_region = self._detect_from_naming(job_name, folder_name)
        if naming_region:
            logger.info(f"[RegionRouter] Region detected from naming: {naming_region}")
            return RegionDetectionResult(
                detected_region=naming_region,
                confidence=0.85,
                reasoning=f"Region inferred from job/folder naming: '{naming_region}'"
            )
        
        # Strategy 3: LLM-based detection (if enabled and multiple regions exist)
        if self.settings.enable_region_detection and self.settings.has_multiple_regions():
            llm_region = await self._detect_via_llm(user_query, job_name, folder_name)
            if llm_region:
                logger.info(f"[RegionRouter] LLM detected region: {llm_region.detected_region}")
                return llm_region
        
        # Strategy 4: Fallback to default region
        default_region = self.settings.get_default_region()
        if default_region:
            logger.warning(
                f"[RegionRouter] Could not detect region, using default: {default_region.name}"
            )
            return RegionDetectionResult(
                detected_region=default_region.name,
                confidence=0.5,
                reasoning="Fallback to default region",
                fallback_used=True
            )
        
        # No regions configured at all
        raise ValueError(
            "No Control-M regions configured. Please set up regions in .env file."
        )
    
    def _detect_explicit_region(self, query: str) -> Optional[str]:
        """Detect explicit region mentions in user query"""
        query_lower = query.lower()
        
        for region_name, keywords in self.region_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return region_name
        
        return None
    
    def _detect_from_naming(
        self,
        job_name: Optional[str],
        folder_name: Optional[str]
    ) -> Optional[str]:
        """Detect region from job/folder naming conventions"""
        
        # Combine job name and folder name for analysis
        naming_text = ""
        if job_name:
            naming_text += job_name.lower() + " "
        if folder_name:
            naming_text += folder_name.lower()
        
        if not naming_text:
            return None
        
        # Check for region prefixes/suffixes in naming
        for region_name, keywords in self.region_keywords.items():
            for keyword in keywords:
                # Check for patterns like: job_us_daily, daily_job_eu, US_Report
                if f"_{keyword}_" in naming_text or \
                   naming_text.startswith(f"{keyword}_") or \
                   naming_text.endswith(f"_{keyword}"):
                    return region_name
        
        return None
    
    async def _detect_via_llm(
        self,
        user_query: str,
        job_name: Optional[str],
        folder_name: Optional[str]
    ) -> Optional[RegionDetectionResult]:
        """Use LLM to detect region based on context"""
        
        if not self.llm:
            return None
        
        # Build region context
        regions_info = "\n".join([
            f"- {r.name}: {r.description or 'No description'}"
            for r in self.settings.regions.values()
        ])
        
        prompt = f"""You are a Control-M region detection assistant. Analyze the user's request and determine which Control-M region they want to interact with.

Available Regions:
{regions_info}

User Query: "{user_query}"
Job Name: {job_name or "Not specified"}
Folder Name: {folder_name or "Not specified"}

Instructions:
1. Analyze the query for geographic indicators (country names, continent names, region codes)
2. Look for business context that might indicate a region (e.g., "US payroll", "European sales")
3. If the query doesn't clearly indicate a region, respond with "UNKNOWN"
4. Respond in JSON format with: region_name, confidence (0.0-1.0), reasoning

Example responses:
{{"region_name": "us-east", "confidence": 0.9, "reasoning": "Query mentions 'US payroll'"}}
{{"region_name": "UNKNOWN", "confidence": 0.0, "reasoning": "No geographic indicators found"}}

Your response:"""
        
        try:
            response = await self.llm.ainvoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Parse JSON response
            import json
            import re
            
            # Extract JSON from response
            json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                if result.get("region_name") and result["region_name"] != "UNKNOWN":
                    region_name = result["region_name"].lower()
                    
                    # Validate region exists
                    if region_name in self.settings.regions:
                        return RegionDetectionResult(
                            detected_region=region_name,
                            confidence=result.get("confidence", 0.7),
                            reasoning=result.get("reasoning", "LLM-based detection")
                        )
            
            return None
        
        except Exception as e:
            logger.error(f"[RegionRouter] LLM region detection failed: {e}", exc_info=True)
            return None
    
    def get_region_config(self, region_name: str) -> Optional[ControlMRegionSettings]:
        """Get region configuration by name"""
        return self.settings.get_region(region_name)
    
    def list_available_regions(self) -> List[Dict[str, Any]]:
        """List all available regions with their details"""
        return [
            {
                "name": config.name,
                "description": config.description,
                "base_url": config.base_url,
                "is_default": config.name == self.settings.default_region
            }
            for config in self.settings.regions.values()
        ]
