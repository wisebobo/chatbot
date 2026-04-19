"""
LLM-powered Wiki Compiler with Knowledge Graph Support
Automatically processes raw documents, extracts knowledge, and generates structured wiki entries
Supports versioning, incremental updates, relationship resolution, and feedback loop
"""
import json
import logging
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.llm.adapter import get_llm_adapter
from app.wiki.engine import (
    LocalWikiEngine, 
    WikiArticle, 
    KnowledgeType, 
    RelationType, 
    EntryStatus,
    SourceReference,
    RelatedEntry,
    UserFeedback
)

logger = logging.getLogger(__name__)


class LLMPoweredWikiCompiler:
    """
    Enhanced LLM-powered Wiki compiler with knowledge graph capabilities
    
    Features:
    - One-shot JSON generation from raw documents
    - Automatic entry_id generation with type-based prefixes
    - Relationship resolution via title matching
    - Version control with history preservation
    - Incremental updates (update/merge/create)
    - Source traceability with auto-generated IDs
    - Confidence scoring based on source quality
    - Document deduplication via content hashing
    """

    # Type abbreviation mapping for entry_id generation
    TYPE_ABBREVIATIONS = {
        "concept": "conc",
        "rule": "rule",
        "process": "proc",
        "case": "case",
        "formula": "form",
        "qa": "qa",
        "event": "event"
    }

    def __init__(self, wiki_engine: Optional[LocalWikiEngine] = None):
        """
        Initialize enhanced LLM-powered Wiki compiler
        
        Args:
            wiki_engine: Local wiki engine instance (creates new if not provided)
        """
        self.wiki_engine = wiki_engine or LocalWikiEngine()
        self.llm_adapter = get_llm_adapter()
        logger.info("Enhanced LLM-powered Wiki Compiler initialized")

    async def compile_document(
        self,
        raw_content: str,
        source_url: Optional[str] = None,
        source_type: str = "text",
        suggested_category: Optional[str] = None,
        force_recompile: bool = False
    ) -> Tuple[WikiArticle, str]:
        """
        Compile a raw document into a structured wiki entry using LLM
        
        Workflow:
        1. Check for existing compilation (deduplication)
        2. Generate complete JSON structure via LLM (one-shot)
        3. Post-process: resolve relationships, generate IDs
        4. Incremental update: create new or update existing entry
        5. Preserve version history
        
        Args:
            raw_content: Raw document content
            source_url: Original source URL or file path
            source_type: Type of source (text, pdf, webpage, docx, etc.)
            suggested_category: Suggested category hint for LLM
            force_recompile: Force recompilation even if document already processed
            
        Returns:
            Tuple of (Compiled WikiArticle, operation_type: 'created' | 'updated' | 'merged')
        """
        # Step 0: Generate document hash for deduplication
        doc_hash = hashlib.md5(raw_content.encode('utf-8')).hexdigest()
        
        # Step 1: Check for existing compilation
        if not force_recompile:
            existing = self._find_existing_article_by_hash(doc_hash)
            if existing:
                logger.info(f"Document already compiled: {existing.title} (v{existing.version})")
                return existing, 'exists'
        
        logger.info(f"Compiling document (source_type={source_type}, length={len(raw_content)})")
        
        try:
            # Step 2: Generate complete JSON structure via LLM
            article_data = await self._generate_wiki_entry_json(raw_content, source_url, suggested_category)
            
            # Step 3: Post-process - resolve relationships and generate IDs
            article_data = await self._post_process_article(article_data, raw_content, source_url, source_type, doc_hash)
            
            # Step 4: Incremental update - create or update
            article, operation = await self._incremental_update(article_data)
            
            logger.info(f"Successfully compiled article: {article.title} (operation={operation}, v{article.version})")
            
            return article, operation
            
        except Exception as e:
            logger.error(f"Failed to compile document: {e}", exc_info=True)
            raise

    async def _generate_wiki_entry_json(
        self, 
        raw_content: str, 
        source_url: Optional[str],
        suggested_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate complete wiki entry JSON structure using LLM (one-shot)
        
        Uses the optimized prompt to generate all fields in a single call
        """
        from langchain_core.messages import HumanMessage
        
        # Truncate content to avoid token limits (keep most relevant parts)
        truncated_content = raw_content[:10000] if len(raw_content) > 10000 else raw_content
        
        category_hint = f"\nSuggested category: {suggested_category}" if suggested_category else ""
        source_hint = f"\nSource URL: {source_url}" if source_url else ""
        
        prompt = f"""You are an expert LLM Wiki structured knowledge engineer. Your task is to analyze the provided document and generate a complete, standardized Wiki knowledge entry in strict JSON format.

### Core Requirements (MUST follow strictly):
1. **Output Format**: ONLY output valid JSON. No explanations, comments, or markdown code blocks.
2. **Schema Compliance**: All required fields must exist with correct types.
3. **Accuracy**: Content must be based solely on the provided text. No fabrication.

### Field Generation Rules:

#### 1. entry_id
- Format: "type_abbreviation_keyword" (lowercase, underscores)
- Type abbreviations: concept→conc, rule→rule, process→proc, case→case, formula→form, qa→qa, event→event
- Keyword: Extract 2-4 key words from title, lowercase, underscore-separated
- Example: "conc_loan_prime_rate", "proc_it_equipment_request"

#### 2. title & aliases
- title: Concise, descriptive title (max 15 words)
- aliases: Array of synonyms, alternative names, common abbreviations (3-8 items)

#### 3. type
- Choose ONE from: concept, rule, process, case, formula, qa, event
- Definitions:
  - concept: Definitions, explanations of terms
  - rule: Policies, regulations, mandatory requirements
  - process: Step-by-step procedures, workflows
  - case: Real-world examples, case studies
  - formula: Mathematical formulas, calculations
  - qa: Question-answer pairs
  - event: Specific incidents, time-bound occurrences

#### 4. content & summary
- content: Well-structured Markdown with headers, lists, bold/italic. Max 2000 words. Include practical examples.
- summary: Concise abstract of 20-50 words capturing core essence.

#### 5. parent_ids & related_ids
- parent_ids: Array of parent entry_ids (leave empty [] if unsure)
- related_ids: Array of objects with:
  - "suggested_title": Title of related concept (we'll resolve to entry_id later)
  - "relation": ONE of: related_to, depends_on, conflict_with, example_of, sub_concept
- If no clear relationships, use empty array []

#### 6. tags
- 5-10 relevant keywords for categorization and search
- Lowercase, no spaces (use hyphens if needed)

#### 7. sources
- Array of source references for traceability
- source_id: Format "doc_" + 6 random alphanumeric characters (e.g., "doc_a3f2b1")
- file_name: Infer from context or use "unknown_document.txt"
- page: Integer if available, otherwise null
- content_snippet: Direct quote (50-150 words) from original text supporting this entry
- url: Use provided source_url if available, otherwise null

#### 8. confidence
- Range: 0.5 to 1.0
- Guidelines:
  - 0.95-1.0: Official policies, authoritative sources, well-documented
  - 0.85-0.94: Standard procedures, verified information
  - 0.75-0.84: General knowledge, reasonable assumptions
  - 0.50-0.74: Unclear sources, ambiguous information

#### 9. status
- Default: "active"

#### 10. version
- Default: 1

#### 11. create_time & update_time
- Current UTC time in ISO 8601 format WITHOUT 'Z' suffix
- Format: "YYYY-MM-DDTHH:MM:SS"
- Example: "2025-10-08T10:30:00"

#### 12. feedback
- Default object: {{"positive": 0, "negative": 0, "comments": []}}

### Input Document:
{truncated_content}{category_hint}{source_hint}

### Output Requirement:
Generate ONLY the JSON object. Ensure:
- Valid JSON syntax (proper commas, quotes, brackets)
- All required fields present
- No extra text before or after JSON
- Ready for direct database storage

### Example Structure (for reference only - generate based on input):
{{
  "entry_id": "conc_example_term",
  "title": "Example Term Definition",
  "aliases": ["alternative name", "abbr"],
  "type": "concept",
  "content": "# Example Term\\n\\nDetailed explanation...",
  "summary": "Brief 20-50 word summary.",
  "parent_ids": [],
  "related_ids": [
    {{
      "suggested_title": "Related Concept",
      "relation": "related_to"
    }}
  ],
  "tags": ["tag1", "tag2", "tag3"],
  "sources": [
    {{
      "source_id": "doc_xyz123",
      "file_name": "source_document.pdf",
      "page": 5,
      "content_snippet": "Direct quote from source...",
      "url": "https://example.com/doc"
    }}
  ],
  "confidence": 0.95,
  "status": "active",
  "version": 1,
  "create_time": "2025-10-08T10:30:00",
  "update_time": "2025-10-08T10:30:00",
  "feedback": {{
    "positive": 0,
    "negative": 0,
    "comments": []
  }}
}}
"""
        
        try:
            response = await self.llm_adapter.ainvoke([HumanMessage(content=prompt)])
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Parse JSON from response
            article_data = self._parse_llm_json_response(content)
            
            if not article_data:
                raise ValueError("Failed to parse valid JSON from LLM response")
            
            logger.info(f"LLM generated entry: {article_data.get('entry_id', 'unknown')}")
            return article_data
            
        except Exception as e:
            logger.error(f"LLM JSON generation failed: {e}")
            raise

    def _parse_llm_json_response(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON from LLM response, handling common formatting issues
        
        Args:
            content: Raw LLM response
            
        Returns:
            Parsed dictionary or None if parsing fails
        """
        import re
        
        try:
            # Strategy 1: Try direct parsing
            return json.loads(content.strip())
        except json.JSONDecodeError:
            pass
        
        try:
            # Strategy 2: Extract JSON from markdown code blocks
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
        
        try:
            # Strategy 3: Find JSON object pattern
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        
        logger.warning(f"Failed to parse JSON from LLM response. Content preview: {content[:200]}")
        return None

    async def _post_process_article(
        self,
        article_data: Dict[str, Any],
        raw_content: str,
        source_url: Optional[str],
        source_type: str,
        doc_hash: str
    ) -> Dict[str, Any]:
        """
        Post-process LLM-generated article data
        
        Tasks:
        1. Resolve related_ids (convert suggested_title to actual entry_id)
        2. Validate and fix field values
        3. Add metadata
        
        Args:
            article_data: Raw LLM output
            raw_content: Original document content
            source_url: Source URL
            source_type: Source type
            doc_hash: Document hash
            
        Returns:
            Processed article data ready for storage
        """
        # Step 1: Resolve relationships
        article_data['related_ids'] = await self._resolve_relationships(
            article_data.get('related_ids', [])
        )
        
        # Step 2: Validate and normalize fields
        article_data = self._validate_and_normalize(article_data)
        
        # Step 3: Add processing metadata
        if 'metadata' not in article_data:
            article_data['metadata'] = {}
        
        article_data['metadata'].update({
            'source_type': source_type,
            'document_hash': doc_hash,
            'compiled_at': datetime.now().isoformat(),
            'compiler_version': '2.0',
        })
        
        return article_data

    async def _resolve_relationships(self, related_ids_raw: List[Dict]) -> List[Dict]:
        """
        Resolve suggested_title to actual entry_id by searching existing articles
        
        Args:
            related_ids_raw: Array of {suggested_title, relation} objects
            
        Returns:
            Array of {entry_id, relation} objects (only resolvable ones)
        """
        resolved = []
        
        for rel in related_ids_raw:
            suggested_title = rel.get('suggested_title', '')
            relation = rel.get('relation', 'related_to')
            
            if not suggested_title:
                continue
            
            # Search for matching article by title or alias
            matched_article = self._find_article_by_title_or_alias(suggested_title)
            
            if matched_article:
                resolved.append({
                    'entry_id': matched_article.entry_id,
                    'relation': relation
                })
                logger.debug(f"Resolved relationship: '{suggested_title}' -> {matched_article.entry_id}")
            else:
                logger.debug(f"Could not resolve relationship for: '{suggested_title}'")
        
        return resolved

    def _find_article_by_title_or_alias(self, title: str) -> Optional[WikiArticle]:
        """
        Find article by exact title match or alias match
        
        Args:
            title: Title to search for
            
        Returns:
            Matching WikiArticle or None
        """
        title_lower = title.lower().strip()
        
        for article in self.wiki_engine.articles.values():
            # Exact title match
            if article.title.lower() == title_lower:
                return article
            
            # Alias match
            if any(alias.lower() == title_lower for alias in article.aliases):
                return article
            
            # Partial title match (fallback)
            if title_lower in article.title.lower() or article.title.lower() in title_lower:
                return article
        
        return None

    def _validate_and_normalize(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize article data fields
        
        Ensures all fields conform to schema requirements
        """
        # Normalize type
        if 'type' in article_data:
            article_data['type'] = article_data['type'].lower()
            if article_data['type'] not in [t.value for t in KnowledgeType]:
                logger.warning(f"Invalid type '{article_data['type']}', defaulting to 'concept'")
                article_data['type'] = 'concept'
        
        # Normalize status
        if 'status' not in article_data or article_data['status'] not in [s.value for s in EntryStatus]:
            article_data['status'] = 'active'
        
        # Ensure confidence is in valid range
        confidence = article_data.get('confidence', 0.9)
        article_data['confidence'] = max(0.5, min(1.0, float(confidence)))
        
        # Ensure version is integer
        article_data['version'] = int(article_data.get('version', 1))
        
        # Normalize timestamps (remove 'Z' suffix if present)
        for time_field in ['create_time', 'update_time']:
            if time_field in article_data:
                ts = article_data[time_field]
                if isinstance(ts, str) and ts.endswith('Z'):
                    article_data[time_field] = ts[:-1]
        
        # Ensure arrays exist
        for array_field in ['aliases', 'tags', 'parent_ids', 'related_ids', 'sources']:
            if array_field not in article_data or not isinstance(article_data[array_field], list):
                article_data[array_field] = []
        
        # Ensure feedback structure
        if 'feedback' not in article_data or not isinstance(article_data['feedback'], dict):
            article_data['feedback'] = {'positive': 0, 'negative': 0, 'comments': []}
        
        return article_data

    async def _incremental_update(self, article_data: Dict[str, Any]) -> Tuple[WikiArticle, str]:
        """
        Perform incremental update: create new or update existing entry
        
        Logic:
        1. Check if entry_id already exists
        2. If exists: increment version, merge content, preserve history
        3. If not exists: create new entry
        
        Args:
            article_data: Processed article data
            
        Returns:
            Tuple of (WikiArticle, operation_type)
        """
        entry_id = article_data['entry_id']
        existing_article = self.wiki_engine.get_article(entry_id)
        
        if existing_article:
            # Update existing entry
            logger.info(f"Updating existing entry: {entry_id} (v{existing_article.version} -> v{existing_article.version + 1})")
            
            # Preserve old version's feedback
            old_feedback = existing_article.feedback
            
            # Merge feedback
            merged_feedback = {
                'positive': old_feedback.positive,
                'negative': old_feedback.negative,
                'comments': old_feedback.comments
            }
            article_data['feedback'] = merged_feedback
            
            # Increment version
            article_data['version'] = existing_article.version + 1
            
            # Update the article
            updated_article = self.wiki_engine.update_article(entry_id, article_data)
            
            if updated_article:
                return updated_article, 'updated'
            else:
                raise RuntimeError(f"Failed to update article {entry_id}")
        else:
            # Create new entry
            logger.info(f"Creating new entry: {entry_id}")
            new_article = self.wiki_engine.add_article(article_data)
            return new_article, 'created'

    def _find_existing_article_by_hash(self, doc_hash: str) -> Optional[WikiArticle]:
        """Find if document was already compiled based on hash"""
        for article in self.wiki_engine.articles.values():
            if article.metadata and article.metadata.get('document_hash') == doc_hash:
                return article
        return None

    async def batch_compile_documents(
        self,
        documents: List[Dict[str, Any]],
        delay_between: float = 1.0
    ) -> List[Tuple[WikiArticle, str]]:
        """
        Compile multiple documents in batch with rate limiting
        
        Args:
            documents: List of dicts with keys: content, source_url, source_type, category
            delay_between: Delay between compilations (seconds)
            
        Returns:
            List of tuples (WikiArticle, operation_type)
        """
        results = []
        import asyncio
        
        for i, doc in enumerate(documents):
            logger.info(f"Processing document {i+1}/{len(documents)}")
            
            try:
                result = await self.compile_document(
                    raw_content=doc['content'],
                    source_url=doc.get('source_url'),
                    source_type=doc.get('source_type', 'text'),
                    suggested_category=doc.get('category'),
                    force_recompile=doc.get('force_recompile', False)
                )
                results.append(result)
                
                # Rate limiting
                if i < len(documents) - 1:
                    await asyncio.sleep(delay_between)
                    
            except Exception as e:
                logger.error(f"Failed to compile document {i+1}: {e}")
                continue
        
        logger.info(f"Batch compilation complete: {len(results)}/{len(documents)} succeeded")
        return results

    async def recompile_low_confidence_articles(
        self,
        confidence_threshold: float = 0.7,
        max_articles: int = 10
    ) -> List[WikiArticle]:
        """
        Recompile articles with low confidence based on user feedback
        
        This implements the feedback loop: when negative feedback accumulates,
        trigger LLM to re-evaluate and improve the content.
        
        Args:
            confidence_threshold: Minimum confidence to skip recompilation
            max_articles: Maximum number of articles to recompile in one batch
            
        Returns:
            List of recompiled articles
        """
        # Find low-confidence articles with negative feedback
        candidates = []
        for article in self.wiki_engine.articles.values():
            total_feedback = article.feedback.positive + article.feedback.negative
            if total_feedback > 0:
                feedback_ratio = article.feedback.positive / total_feedback
                if article.confidence < confidence_threshold or feedback_ratio < 0.5:
                    candidates.append(article)
        
        # Sort by lowest confidence first
        candidates.sort(key=lambda x: x.confidence)
        candidates = candidates[:max_articles]
        
        if not candidates:
            logger.info("No low-confidence articles found for recompilation")
            return []
        
        logger.info(f"Recompiling {len(candidates)} low-confidence articles")
        
        recompiled = []
        for article in candidates:
            try:
                # Get original source content (if available)
                source_content = self._get_source_content(article)
                if not source_content:
                    logger.warning(f"No source content for {article.entry_id}, skipping")
                    continue
                
                # Recompile
                new_article, operation = await self.compile_document(
                    raw_content=source_content,
                    source_url=article.sources[0].url if article.sources else None,
                    force_recompile=True
                )
                recompiled.append(new_article)
                
            except Exception as e:
                logger.error(f"Failed to recompile {article.entry_id}: {e}")
                continue
        
        logger.info(f"Recompilation complete: {len(recompiled)} articles updated")
        return recompiled

    def _get_source_content(self, article: WikiArticle) -> Optional[str]:
        """
        Retrieve original source content for an article
        
        In production, this would fetch from document storage system.
        For now, we use the content snippet from sources as fallback.
        """
        if article.sources:
            # Return concatenated content snippets
            snippets = [src.content_snippet for src in article.sources]
            return "\n\n".join(snippets)
        return None

    def generate_knowledge_graph_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive report on the knowledge graph
        
        Returns statistics about:
        - Total articles by type
        - Relationship density
        - Average confidence
        - Feedback distribution
        - Version distribution
        """
        articles = list(self.wiki_engine.articles.values())
        
        if not articles:
            return {"error": "No articles in knowledge base"}
        
        # Statistics
        stats = {
            "total_articles": len(articles),
            "by_type": {},
            "by_status": {},
            "avg_confidence": 0.0,
            "total_relationships": 0,
            "avg_version": 0.0,
            "feedback_summary": {
                "total_positive": 0,
                "total_negative": 0,
                "articles_with_feedback": 0
            }
        }
        
        # Calculate statistics
        total_confidence = 0.0
        total_version = 0
        total_relationships = 0
        
        for article in articles:
            # By type
            type_key = article.type.value if isinstance(article.type, KnowledgeType) else article.type
            stats["by_type"][type_key] = stats["by_type"].get(type_key, 0) + 1
            
            # By status
            status_key = article.status.value if isinstance(article.status, EntryStatus) else article.status
            stats["by_status"][status_key] = stats["by_status"].get(status_key, 0) + 1
            
            # Confidence
            total_confidence += article.confidence
            
            # Version
            total_version += article.version
            
            # Relationships
            total_relationships += len(article.related_ids)
            
            # Feedback
            stats["feedback_summary"]["total_positive"] += article.feedback.positive
            stats["feedback_summary"]["total_negative"] += article.feedback.negative
            if article.feedback.positive > 0 or article.feedback.negative > 0:
                stats["feedback_summary"]["articles_with_feedback"] += 1
        
        # Averages
        stats["avg_confidence"] = round(total_confidence / len(articles), 3)
        stats["avg_version"] = round(total_version / len(articles), 2)
        stats["total_relationships"] = total_relationships
        
        return stats
