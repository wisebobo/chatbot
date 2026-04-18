"""
Wiki module - LLM-powered wiki knowledge base system
Provides automated document compilation and structured article generation
"""
from app.wiki.engine import LocalWikiEngine, WikiArticle
from app.wiki.sample_data import get_sample_articles
from app.wiki.compiler import LLMPoweredWikiCompiler

__all__ = [
    "LocalWikiEngine", 
    "WikiArticle", 
    "get_sample_articles",
    "LLMPoweredWikiCompiler"
]
