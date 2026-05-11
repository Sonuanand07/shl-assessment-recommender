"""
Catalog loading and processing module.
Handles loading the SHL product catalog with robust error handling.
"""

import json
import logging
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class CatalogManager:
    """Manages loading and querying the SHL product catalog."""
    
    def __init__(self, catalog_path: str = "shl_product_catalog.json"):
        self.catalog_path = catalog_path
        self.items: List[Dict[str, Any]] = []
        self.items_by_id: Dict[str, Dict[str, Any]] = {}
        self.items_by_name: Dict[str, Dict[str, Any]] = {}
        self.load_catalog()
    
    def load_catalog(self) -> None:
        """Load and parse the catalog with robust error handling."""
        try:
            # Try standard JSON first with cleanup
            self._load_with_json_fallback()
        except Exception as e:
            logger.warning(f"JSON fallback failed: {e}. Trying line-by-line parsing.")
            try:
                self._load_line_by_line()
            except Exception as e2:
                logger.error(f"All catalog loading methods failed: {e2}")
                raise
    
    def _load_with_json_fallback(self) -> None:
        """Fallback: load JSON with error handling and repair."""
        try:
            with open(self.catalog_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Remove control characters but preserve valid ones
            content = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', ' ', content)
            
            data = json.loads(content)
            for item in data:
                self._add_item(item)
        except Exception as e:
            logger.error(f"JSON fallback failed: {e}")
            # Try line-by-line parsing as last resort
            self._load_line_by_line()
    
    def _load_line_by_line(self) -> None:
        """Last resort: parse JSON objects line by line with aggressive repair."""
        try:
            with open(self.catalog_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Remove problematic control characters but preserve structure
            # Keep only: newline, tab, printable ASCII, and valid Unicode
            content = ''.join(
                char if ord(char) >= 32 or char in '\n\r\t' else ' '
                for char in content
            )
            
            # Extract JSON objects from the array
            content = content.strip()
            if content.startswith('['):
                content = content[1:]
            if content.endswith(']'):
                content = content[:-1]
            
            # Split by common patterns and try to parse
            depth = 0
            current = ""
            successful = 0
            
            for char in content:
                if char == '{':
                    depth += 1
                    current += char
                elif char == '}':
                    depth -= 1
                    current += char
                    if depth == 0 and current.strip():
                        try:
                            # Try to parse as is
                            item = json.loads(current)
                            self._add_item(item)
                            successful += 1
                        except json.JSONDecodeError:
                            # Try to fix common issues
                            try:
                                # Remove trailing commas before closing braces
                                fixed = current.replace(',}', '}').replace(',]', ']')
                                item = json.loads(fixed)
                                self._add_item(item)
                                successful += 1
                            except:
                                logger.debug(f"Failed to parse JSON object")
                        current = ""
                else:
                    if depth > 0:
                        current += char
            
            if successful == 0:
                logger.warning("No JSON objects successfully parsed from file")
                raise ValueError("Failed to extract any valid JSON objects")
            else:
                logger.info(f"Successfully parsed {successful} JSON objects from catalog")
        
        except Exception as e:
            logger.error(f"Line-by-line parsing failed: {e}")
            raise
    
    def _add_item(self, item: Dict[str, Any]) -> None:
        """Add an item to the catalog."""
        if not item or 'name' not in item:
            return
        
        self.items.append(item)
        if 'entity_id' in item:
            self.items_by_id[item['entity_id']] = item
        self.items_by_name[item['name']] = item
    
    def search_by_keywords(self, keywords: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Search catalog by keywords in name and description."""
        keywords_lower = [k.lower() for k in keywords]
        results = []
        
        for item in self.items:
            name_lower = item.get('name', '').lower()
            desc_lower = item.get('description', '').lower()
            keys = [k.lower() for k in item.get('keys', [])]
            
            score = 0
            for keyword in keywords_lower:
                if keyword in name_lower:
                    score += 3
                if keyword in desc_lower:
                    score += 1
                if any(keyword in k for k in keys):
                    score += 2
            
            if score > 0:
                results.append((score, item))
        
        # Sort by score descending
        results.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in results[:limit]]
    
    def search_by_job_level(self, job_levels: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Search catalog by job level."""
        results = []
        job_levels_lower = [j.lower() for j in job_levels]
        
        for item in self.items:
            item_levels = [j.lower() for j in item.get('job_levels', [])]
            if any(level in item_levels for level in job_levels_lower):
                results.append(item)
        
        return results[:limit]
    
    def search_by_assessment_type(self, assessment_types: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Search catalog by assessment type/keys."""
        results = []
        types_lower = [t.lower() for t in assessment_types]
        
        for item in self.items:
            item_keys = [k.lower() for k in item.get('keys', [])]
            if any(t in item_keys for t in types_lower):
                results.append(item)
        
        return results[:limit]
    
    def get_item_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a catalog item by name."""
        return self.items_by_name.get(name)
    
    def get_item_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get a catalog item by entity ID."""
        return self.items_by_id.get(entity_id)
    
    def get_all_items(self) -> List[Dict[str, Any]]:
        """Get all catalog items."""
        return self.items
    
    def get_assessment_types(self) -> set:
        """Get all unique assessment types/keys in catalog."""
        types = set()
        for item in self.items:
            types.update(item.get('keys', []))
        return types
    
    def get_job_levels(self) -> set:
        """Get all unique job levels in catalog."""
        levels = set()
        for item in self.items:
            levels.update(item.get('job_levels', []))
        return levels
    
    def get_languages(self) -> set:
        """Get all unique languages in catalog."""
        languages = set()
        for item in self.items:
            languages.update(item.get('languages', []))
        return languages


# Global catalog instance
_catalog_manager: Optional[CatalogManager] = None


def get_catalog() -> CatalogManager:
    """Get or initialize the global catalog manager."""
    global _catalog_manager
    if _catalog_manager is None:
        _catalog_manager = CatalogManager()
    return _catalog_manager
