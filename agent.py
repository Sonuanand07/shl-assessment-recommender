"""
Conversational agent for SHL assessment recommendations.
Handles clarification, recommendations, refinement, and comparison.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from catalog import get_catalog

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent conversation state."""
    GATHERING_CONTEXT = "gathering"
    READY_TO_RECOMMEND = "ready"
    COMPARING = "comparing"
    COMPLETE = "complete"


class ConversationContext:
    """Maintains context throughout a conversation."""
    
    def __init__(self):
        self.job_title: Optional[str] = None
        self.job_levels: List[str] = []
        self.experience_years: Optional[int] = None
        self.assessment_types: List[str] = []  # Personality, Knowledge, Ability, etc.
        self.skills_needed: List[str] = []
        self.industry: Optional[str] = None
        self.purpose: Optional[str] = None  # selection, development, etc.
        self.use_case: Optional[str] = None
        self.comparison_items: List[str] = []
        self.turn_count: int = 0
        self.state: AgentState = AgentState.GATHERING_CONTEXT
        self.extracted_constraints: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dict for analysis."""
        return {
            'job_title': self.job_title,
            'job_levels': self.job_levels,
            'experience_years': self.experience_years,
            'assessment_types': self.assessment_types,
            'skills_needed': self.skills_needed,
            'industry': self.industry,
            'purpose': self.purpose,
            'use_case': self.use_case
        }


class AssessmentRecommender:
    """Main agent for conversational assessment recommendations."""
    
    # Mapping of common terms to assessment types
    ASSESSMENT_TYPE_MAPPING = {
        'personality': ['Personality & Behavior', 'OPQ32r', 'personality assessment'],
        'knowledge': ['Knowledge & Skills', 'technical', 'skills test'],
        'ability': ['Ability & Aptitude', 'reasoning', 'iq test'],
        'situational': ['Biodata & Situational Judgment', 'situational judgment'],
        'motivation': ['Motivation'],
        'competency': ['Competencies'],
        'development': ['Development & 360'],
        'leadership': ['Leadership', 'executive'],
        'interview': ['Interview'],
    }
    
    JOB_LEVEL_MAPPING = {
        'entry': ['Entry-Level', 'graduate', 'junior'],
        'mid': ['Mid-Professional', 'mid-level'],
        'senior': ['Professional Individual Contributor'],
        'manager': ['Manager', 'supervisor', 'front line manager'],
        'director': ['Director'],
        'executive': ['Executive', 'cxo', 'ceo'],
    }
    
    def __init__(self):
        self.catalog = get_catalog()
        self.context = ConversationContext()
    
    def process_message(self, user_message: str, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Process a user message and return agent response.
        
        Args:
            user_message: Current user message
            conversation_history: Full conversation history
        
        Returns:
            Dict with 'reply', 'recommendations', 'end_of_conversation'
        """
        self.context.turn_count = len(conversation_history) // 2  # Approximate turn count
        
        # Extract information from user message
        self._extract_context(user_message, conversation_history)
        
        # Determine agent action
        if self._should_refuse(user_message):
            return self._refuse_response()
        
        if self._is_comparison_request(user_message):
            return self._handle_comparison(user_message)
        
        # Check if we have enough context to recommend
        if self._has_sufficient_context():
            recommendations = self._generate_recommendations()
            if recommendations:
                self.context.state = AgentState.READY_TO_RECOMMEND
                return self._recommendation_response(recommendations, user_message)
        
        # Need more clarification
        return self._clarification_response(user_message)
    
    def _extract_context(self, message: str, conversation_history: List[Dict[str, str]]) -> None:
        """Extract context from user message and history."""
        message_lower = message.lower()
        
        # Extract job title
        if any(title in message_lower for title in ['developer', 'engineer', 'analyst', 'manager', 'leader', 'designer']):
            self.context.job_title = message
        
        # Extract experience level
        for level, keywords in self.JOB_LEVEL_MAPPING.items():
            for keyword in keywords:
                if keyword.lower() in message_lower:
                    if level == 'entry':
                        self.context.job_levels.append('Entry-Level')
                    elif level == 'mid':
                        self.context.job_levels.append('Mid-Professional')
                    elif level == 'senior':
                        self.context.job_levels.append('Professional Individual Contributor')
                    elif level == 'manager':
                        self.context.job_levels.append('Manager')
                    elif level == 'director':
                        self.context.job_levels.append('Director')
                    elif level == 'executive':
                        self.context.job_levels.append('Executive')
        
        # Extract years of experience
        years_match = re.search(r'(\d+)\s*(?:years?|yrs?)', message_lower)
        if years_match:
            self.context.experience_years = int(years_match.group(1))
        
        # Extract purpose
        if any(word in message_lower for word in ['selection', 'hiring', 'screening', 'evaluate']):
            self.context.purpose = 'selection'
        elif any(word in message_lower for word in ['development', 'develop', 'improve', 'growth', 'feedback']):
            self.context.purpose = 'development'
        elif any(word in message_lower for word in ['benchmark', 'benchmarking']):
            self.context.purpose = 'benchmarking'
        
        # Extract assessment types
        for atype, keywords in self.ASSESSMENT_TYPE_MAPPING.items():
            for keyword in keywords:
                if keyword.lower() in message_lower:
                    if atype == 'personality':
                        if 'Personality & Behavior' not in self.context.assessment_types:
                            self.context.assessment_types.append('Personality & Behavior')
                    elif atype == 'knowledge':
                        if 'Knowledge & Skills' not in self.context.assessment_types:
                            self.context.assessment_types.append('Knowledge & Skills')
                    elif atype == 'ability':
                        if 'Ability & Aptitude' not in self.context.assessment_types:
                            self.context.assessment_types.append('Ability & Aptitude')
                    elif atype == 'situational':
                        if 'Biodata & Situational Judgment' not in self.context.assessment_types:
                            self.context.assessment_types.append('Biodata & Situational Judgment')
        
        # Extract skills mentioned
        skills = re.findall(r'(?:skill|expertise|proficiency|knowledge)\s+in\s+(\w+)', message_lower)
        if skills:
            self.context.skills_needed.extend(skills)
    
    def _should_refuse(self, message: str) -> bool:
        """Check if message should trigger a refusal."""
        message_lower = message.lower()
        
        # Refuse off-topic requests
        if any(word in message_lower for word in [
            'general hiring', 'legal', 'law', 'policy', 'hr', 'salary', 'compensation',
            'interview tips', 'hiring advice', 'how to hire', 'prompt injection', 'jailbreak'
        ]):
            return True
        
        # Refuse if asking for external data
        if any(word in message_lower for word in ['external', 'outside catalog', 'other assessments']):
            return True
        
        return False
    
    def _is_comparison_request(self, message: str) -> bool:
        """Check if user is asking for comparison."""
        message_lower = message.lower()
        return any(word in message_lower for word in ['difference', 'compare', 'vs', 'versus', 'which is better'])
    
    def _has_sufficient_context(self) -> bool:
        """Check if we have enough context to make recommendations."""
        # Need at least some of: job level, purpose, assessment type, or skills
        return bool(
            self.context.job_levels or 
            self.context.purpose or 
            self.context.assessment_types or
            (self.context.job_title and len(self.context.job_title) > 5)
        )
    
    def _generate_recommendations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Generate assessment recommendations based on context."""
        all_items = self.catalog.get_all_items()
        scored_items = []
        
        for item in all_items:
            score = 0
            
            # Score by job level match
            if self.context.job_levels:
                item_levels = item.get('job_levels', [])
                for level in self.context.job_levels:
                    if level in item_levels:
                        score += 10
            
            # Score by assessment type match
            if self.context.assessment_types:
                item_keys = item.get('keys', [])
                for atype in self.context.assessment_types:
                    if atype in item_keys:
                        score += 8
            
            # Score by keywords in name/description
            if self.context.skills_needed:
                name_desc = (item.get('name', '') + ' ' + item.get('description', '')).lower()
                for skill in self.context.skills_needed:
                    if skill.lower() in name_desc:
                        score += 5
            
            # Score by job title keywords
            if self.context.job_title:
                name_desc = (item.get('name', '') + ' ' + item.get('description', '')).lower()
                title_lower = self.context.job_title.lower()
                # Look for specific tech terms
                if any(tech in name_desc for tech in title_lower.split()):
                    score += 3
            
            if score > 0:
                scored_items.append((score, item))
        
        # Sort and return top items
        scored_items.sort(key=lambda x: x[0], reverse=True)
        recommendations = [item for _, item in scored_items[:limit]]
        
        return recommendations
    
    def _format_recommendation(self, item: Dict[str, Any]) -> Dict[str, str]:
        """Format a single recommendation."""
        return {
            'name': item.get('name', 'Unknown'),
            'url': item.get('link', ''),
            'test_type': self._get_test_type_code(item.get('keys', [])),
            'keys': ', '.join(item.get('keys', [])),
            'duration': item.get('duration', '-'),
            'languages': self._format_languages(item.get('languages', []))
        }
    
    def _format_languages(self, languages: list) -> str:
        """Format languages list for display."""
        if not languages:
            return '-'
        if len(languages) <= 3:
            return ', '.join(languages)
        else:
            return ', '.join(languages[:3]) + f" _(+{len(languages)-3} more)_"
    
    def _get_test_type_code(self, keys: List[str]) -> str:
        """Get single letter code for test type."""
        if not keys:
            return 'O'
        
        key = keys[0].lower()
        if 'personality' in key or 'behavior' in key:
            return 'P'
        elif 'knowledge' in key or 'skills' in key:
            return 'K'
        elif 'ability' in key or 'aptitude' in key:
            return 'A'
        elif 'situational' in key or 'judgment' in key:
            return 'S'
        elif 'motivation' in key:
            return 'M'
        elif 'competency' in key or 'competencies' in key:
            return 'C'
        elif 'development' in key or '360' in key:
            return 'D'
        else:
            return 'O'
    
    def _handle_comparison(self, message: str) -> Dict[str, Any]:
        """Handle comparison requests."""
        # Extract assessment names to compare
        comparison_terms = re.findall(r'(?:between|vs|versus|and)\s+(\w+)\s+(?:and|vs|\?)', message, re.IGNORECASE)
        
        comparison_info = "I can compare assessments from our catalog. "
        
        # Find items matching the comparison terms
        matched_items = []
        for term in comparison_terms:
            for item in self.catalog.get_all_items():
                if term.lower() in item.get('name', '').lower():
                    matched_items.append(item)
        
        if len(matched_items) >= 2:
            # Generate comparison
            comparison_info += "Here's what differs:\n"
            for i, item in enumerate(matched_items[:2], 1):
                comparison_info += f"\n{i}. {item.get('name')} - {item.get('description', 'No description')[:100]}..."
        else:
            comparison_info += "Could you specify which assessments you'd like to compare?"
        
        return {
            'reply': comparison_info,
            'recommendations': [],
            'end_of_conversation': False
        }
    
    def _refuse_response(self) -> Dict[str, Any]:
        """Generate refusal response."""
        return {
            'reply': "I'm focused on SHL assessment recommendations. I can't help with general hiring advice, legal matters, or assessments outside the SHL catalog. What specific SHL assessment might help your hiring need?",
            'recommendations': [],
            'end_of_conversation': False
        }
    
    def _recommendation_response(self, recommendations: List[Dict[str, Any]], user_message: str) -> Dict[str, Any]:
        """Generate recommendation response."""
        if not recommendations:
            return {
                'reply': "I don't have matching assessments in the catalog for your requirements. Could you provide more details about the role or skills you're evaluating?",
                'recommendations': [],
                'end_of_conversation': False
            }
        
        num_recs = min(len(recommendations), 10)
        formatted_recs = [self._format_recommendation(item) for item in recommendations[:num_recs]]
        
        # Generate contextual response with assessment details
        context_parts = []
        if self.context.job_title:
            context_parts.append(f"{self.context.job_title}")
        if self.context.job_levels:
            context_parts.append(f"({', '.join(self.context.job_levels)})")
        if self.context.purpose:
            context_parts.append(f"for {self.context.purpose}")
        
        context_str = " ".join(context_parts)
        
        reply = f"For your needs{' - ' + context_str if context_str else ''}, here are {num_recs} relevant assessments:"
        
        return {
            'reply': reply,
            'recommendations': formatted_recs,
            'end_of_conversation': False
        }
    
    def _clarification_response(self, user_message: str) -> Dict[str, Any]:
        """Generate clarification request."""
        message_lower = user_message.lower()
        
        if not self.context.job_title or len(self.context.job_title) < 3:
            return {
                'reply': "Let's start by understanding your hiring need. What role are you filling?",
                'recommendations': [],
                'end_of_conversation': False
            }
        
        if not self.context.job_levels and 'level' not in message_lower and 'senior' not in message_lower:
            return {
                'reply': "What seniority level? Entry-level, mid, senior, manager, director, or executive?",
                'recommendations': [],
                'end_of_conversation': False
            }
        
        if not self.context.purpose and 'selection' not in message_lower and 'development' not in message_lower and 'screen' not in message_lower:
            return {
                'reply': "What's the primary purpose? Screening candidates, development feedback, or benchmarking?",
                'recommendations': [],
                'end_of_conversation': False
            }
        
        # If we have enough context, generate recommendations
        return {
            'reply': "I have enough information. Let me build a shortlist based on your needs.",
            'recommendations': [],
            'end_of_conversation': False
        }


def create_agent() -> AssessmentRecommender:
    """Factory function to create a new agent."""
    return AssessmentRecommender()
