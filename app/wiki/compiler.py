"""
LLM-powered Wiki Compiler
Automatically processes raw documents, extracts knowledge, and generates structured wiki articles
"""
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.llm.adapter import get_llm_adapter
from app.wiki.engine import LocalWikiEngine, WikiArticle

logger = logging.getLogger(__name__)


class LLMPoweredWikiCompiler:
    """
    LLM-powered Wiki compiler that automatically transforms raw documents into structured wiki articles
    
    Workflow:
    1. Ingest raw documents (text, PDFs, web pages)
    2. Use LLM to analyze and extract key information
    3. Generate structured markdown with summaries, cross-links, and indexes
    4. Store in local wiki engine
    5. Continuously update as new documents arrive
    """

    def __init__(self, wiki_engine: Optional[LocalWikiEngine] = None):
        """
        Initialize LLM-powered Wiki compiler
        
        Args:
            wiki_engine: Local wiki engine instance (creates new if not provided)
        """
        self.wiki_engine = wiki_engine or LocalWikiEngine()
        self.llm_adapter = get_llm_adapter()
        logger.info("LLM-powered Wiki Compiler initialized")

    async def compile_document(
        self,
        raw_content: str,
        source_url: Optional[str] = None,
        source_type: str = "text",
        category: Optional[str] = None,
        force_recompile: bool = False
    ) -> WikiArticle:
        """
        Compile a raw document into a structured wiki article using LLM
        
        Args:
            raw_content: Raw document content (text, extracted from PDF/web, etc.)
            source_url: Original source URL or file path
            source_type: Type of source (text, pdf, webpage, docx, etc.)
            category: Suggested category (optional, LLM can auto-detect)
            force_recompile: Force recompilation even if document already processed
            
        Returns:
            Compiled WikiArticle
        """
        # Generate document hash to detect changes
        doc_hash = hashlib.md5(raw_content.encode('utf-8')).hexdigest()
        
        # Check if already compiled (unless force recompile)
        if not force_recompile:
            existing = self._find_existing_article(doc_hash)
            if existing:
                logger.info(f"Document already compiled: {existing.title}")
                return existing
        
        logger.info(f"Compiling document (source_type={source_type}, length={len(raw_content)})")
        
        try:
            # Step 1: Extract structure and key information using LLM
            structured_data = await self._extract_structure(raw_content, category)
            
            # Step 2: Generate optimized markdown wiki article
            wiki_content = await self._generate_wiki_article(structured_data, raw_content)
            
            # Step 3: Extract metadata and tags
            metadata = await self._extract_metadata(structured_data, raw_content)
            
            # Step 4: Find related articles for cross-linking
            related_articles = self._find_related_articles(metadata.get('tags', []), metadata.get('category'))
            
            # Step 5: Add cross-references to the article
            wiki_content = self._add_cross_references(wiki_content, related_articles)
            
            # Step 6: Create wiki article
            article_data = {
                "title": structured_data.get('title', 'Untitled Article'),
                "content": wiki_content,
                "category": metadata.get('category', category or 'General'),
                "tags": metadata.get('tags', []),
                "url": source_url,
                "author": "LLM Wiki Compiler",
                "version": "1.0",
                "metadata": {
                    **metadata,
                    "source_type": source_type,
                    "document_hash": doc_hash,
                    "compiled_at": datetime.now().isoformat(),
                    "related_articles": [art.id for art in related_articles],
                }
            }
            
            article = self.wiki_engine.add_article(article_data)
            logger.info(f"Successfully compiled article: {article.title}")
            
            return article
            
        except Exception as e:
            logger.error(f"Failed to compile document: {e}", exc_info=True)
            raise

    async def _extract_structure(self, raw_content: str, suggested_category: Optional[str] = None) -> Dict[str, Any]:
        """
        Use LLM to extract document structure and key information
        
        Returns dict with:
        - title: Suggested article title
        - sections: List of section headers and summaries
        - key_points: Main takeaways
        - category: Detected category
        """
        from langchain_core.messages import HumanMessage
        
        prompt = f"""
You are an expert knowledge architect. Analyze the following document and extract its structure.

DOCUMENT CONTENT:
{raw_content[:8000]}  # Limit to avoid token limits

TASK:
Extract the following information in JSON format:
1. A concise, descriptive title (max 10 words)
2. Main sections with brief summaries
3. Key points/takeaways (bullet points)
4. Appropriate category (choose from: HR, IT, Finance, Engineering, Operations, Legal, Marketing, Sales, General)
5. Relevant tags (5-10 keywords)

OUTPUT FORMAT (JSON only, no other text):
{{
  "title": "Descriptive Title",
  "sections": [
    {{
      "heading": "Section 1",
      "summary": "Brief summary of this section"
    }}
  ],
  "key_points": [
    "Key point 1",
    "Key point 2"
  ],
  "category": "Category Name",
  "tags": ["tag1", "tag2", "tag3"]
}}

If suggested category is provided ({suggested_category}), consider it but use your judgment for the best fit.
"""
        
        try:
            response = await self.llm_adapter.ainvoke([HumanMessage(content=prompt)])
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Parse JSON from response (handle potential markdown formatting)
            import json
            import re
            
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                structured_data = json.loads(json_match.group())
            else:
                # Fallback: try parsing entire content as JSON
                structured_data = json.loads(content)
            
            return structured_data
            
        except Exception as e:
            logger.warning(f"LLM structure extraction failed, using fallback: {e}")
            # Fallback: basic extraction
            return {
                "title": raw_content[:100].split('\n')[0] if '\n' in raw_content else "Untitled Document",
                "sections": [],
                "key_points": [],
                "category": suggested_category or "General",
                "tags": []
            }

    async def _generate_wiki_article(self, structured_data: Dict[str, Any], original_content: str) -> str:
        """
        Generate a well-formatted markdown wiki article from structured data
        
        Returns formatted markdown string
        """
        from langchain_core.messages import HumanMessage
        
        prompt = f"""
You are a professional technical writer. Create a comprehensive, well-structured wiki article in Markdown format.

ARTICLE STRUCTURE:
Title: {structured_data.get('title', 'Untitled')}
Category: {structured_data.get('category', 'General')}
Sections: {structured_data.get('sections', [])}
Key Points: {structured_data.get('key_points', [])}

ORIGINAL CONTENT (for reference):
{original_content[:6000]}

REQUIREMENTS:
1. Write in clear, professional English
2. Use proper Markdown formatting (headers, lists, bold, italics)
3. Start with a concise summary/overview paragraph
4. Organize content into logical sections with clear headings
5. Include practical examples where helpful
6. Add a "Related Topics" section at the end (leave placeholder: "[Related articles will be linked here]")
7. Keep content scannable and easy to read
8. Focus on actionable information
9. Maximum 2000 words

OUTPUT: Pure Markdown content only (no explanations, no JSON wrapper)
"""
        
        try:
            response = await self.llm_adapter.ainvoke([HumanMessage(content=prompt)])
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Clean up response (remove any markdown code block markers)
            content = content.strip()
            if content.startswith('``'):
                content = content[3:]
            if content.endswith('``'):
                content = content[:-3]
            
            return content.strip()
            
        except Exception as e:
            logger.warning(f"LLM article generation failed, using fallback: {e}")
            # Fallback: simple formatting
            return f"# {structured_data.get('title', 'Untitled')}\n\n{original_content[:2000]}"

    async def _extract_metadata(self, structured_data: Dict[str, Any], original_content: str) -> Dict[str, Any]:
        """
        Extract additional metadata from the document
        
        Returns metadata dictionary
        """
        # For now, use structured data directly
        # Could enhance with additional LLM calls for more detailed metadata
        return {
            "category": structured_data.get('category', 'General'),
            "tags": structured_data.get('tags', []),
            "word_count": len(original_content.split()),
            "has_examples": "example" in original_content.lower() or "case" in original_content.lower(),
            "complexity": "high" if len(original_content) > 5000 else "medium" if len(original_content) > 2000 else "low",
        }

    def _find_existing_article(self, doc_hash: str) -> Optional[WikiArticle]:
        """Find if document was already compiled based on hash"""
        for article in self.wiki_engine.articles.values():
            if article.metadata and article.metadata.get('document_hash') == doc_hash:
                return article
        return None

    def _find_related_articles(self, tags: List[str], category: Optional[str]) -> List[WikiArticle]:
        """Find related articles based on tags and category"""
        related = []
        
        for article in self.wiki_engine.articles.values():
            score = 0
            
            # Category match
            if category and article.category == category:
                score += 2
            
            # Tag overlap
            if tags and article.tags:
                common_tags = set(tags) & set(article.tags)
                score += len(common_tags) * 1.5
            
            if score > 0:
                related.append((article, score))
        
        # Sort by relevance score and return top 5
        related.sort(key=lambda x: x[1], reverse=True)
        return [art for art, score in related[:5]]

    def _add_cross_references(self, content: str, related_articles: List[WikiArticle]) -> str:
        """Add cross-reference links to related articles"""
        if not related_articles:
            return content
        
        # Replace placeholder with actual links
        cross_refs_section = "\n\n## Related Articles\n\n"
        for article in related_articles:
            cross_refs_section += f"- [{article.title}](/wiki/{article.id}) - {article.category}\n"
        
        # Replace placeholder or append
        if "[Related articles will be linked here]" in content:
            content = content.replace("[Related articles will be linked here]", cross_refs_section.strip())
        else:
            content += cross_refs_section
        
        return content

    async def batch_compile_documents(
        self,
        documents: List[Dict[str, Any]],
        delay_between: float = 1.0
    ) -> List[WikiArticle]:
        """
        Compile multiple documents in batch
        
        Args:
            documents: List of dicts with keys: content, source_url, source_type, category
            delay_between: Delay between compilations (seconds) to avoid rate limits
            
        Returns:
            List of compiled WikiArticles
        """
        results = []
        import asyncio
        
        for i, doc in enumerate(documents):
            logger.info(f"Processing document {i+1}/{len(documents)}")
            
            try:
                article = await self.compile_document(
                    raw_content=doc['content'],
                    source_url=doc.get('source_url'),
                    source_type=doc.get('source_type', 'text'),
                    category=doc.get('category'),
                )
                results.append(article)
                
                # Rate limiting
                if i < len(documents) - 1:
                    await asyncio.sleep(delay_between)
                    
            except Exception as e:
                logger.error(f"Failed to compile document {i+1}: {e}")
                continue
        
        logger.info(f"Batch compilation complete: {len(results)}/{len(documents)} succeeded")
        return results

    def generate_index(self) -> str:
        """
        Generate a comprehensive index of all wiki articles
        
        Returns formatted markdown index
        """
        articles = list(self.wiki_engine.articles.values())
        
        if not articles:
            return "# Wiki Index\n\nNo articles available yet."
        
        # Group by category
        categories = {}
        for article in articles:
            cat = article.category or "Uncategorized"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(article)
        
        # Build index
        index = "# Wiki Knowledge Base Index\n\n"
        index += f"**Total Articles:** {len(articles)}\n"
        index += f"**Categories:** {len(categories)}\n\n"
        index += "---\n\n"
        
        for category in sorted(categories.keys()):
            cat_articles = sorted(categories[category], key=lambda x: x.title)
            index += f"## {category}\n\n"
            
            for article in cat_articles:
                tags_str = ", ".join(article.tags[:5]) if article.tags else "No tags"
                index += f"### [{article.title}](/wiki/{article.id})\n"
                index += f"- **Tags:** {tags_str}\n"
                index += f"- **Last Updated:** {article.updated_at[:10]}\n"
                
                # Extract first line of content as preview
                preview = article.content.split('\n')[0][:150]
                index += f"- **Preview:** {preview}...\n\n"
            
            index += "---\n\n"
        
        return index
