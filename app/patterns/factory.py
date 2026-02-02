"""
Factory Pattern Implementation
JobCardFactory creates schematic job advertisements for conjoint experiments
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
from bson import ObjectId
from app.models.job_attribute import JobAttribute
from app.models.generated_job_card import GeneratedJobCard
from app.services.attribute_service import AttributeService


class JobCardBuilder:
    """
    Builder pattern for constructing job cards step by step.
    """
    
    def __init__(self):
        self._attributes = {}
        self._rendered_text = ""
    
    def set_attribute(self, key: str, level_id: str) -> 'JobCardBuilder':
        """Set a job attribute."""
        self._attributes[key] = level_id
        return self
    
    def set_attributes(self, attributes: Dict[str, str]) -> 'JobCardBuilder':
        """Set multiple attributes at once."""
        self._attributes.update(attributes)
        return self
    
    def build_rendered_text(self, attribute_definitions: List[JobAttribute]) -> 'JobCardBuilder':
        """Build human-readable text from attributes."""
        lines = []
        
        for attr_def in attribute_definitions:
            if attr_def.attribute_key in self._attributes:
                level_id = self._attributes[attr_def.attribute_key]
                display_text = attr_def.get_level_text(level_id)
                lines.append(f"**{attr_def.display_name}**: {display_text}")
        
        self._rendered_text = "\n".join(lines)
        return self
    
    def build(self, session_id: ObjectId, card_label: str, 
              round_number: int) -> GeneratedJobCard:
        """Build the final job card."""
        return GeneratedJobCard(
            session_id=session_id,
            card_label=card_label,
            attributes=self._attributes.copy(),
            rendered_text=self._rendered_text,
            round_number=round_number
        )
    
    def reset(self):
        """Reset builder for reuse."""
        self._attributes = {}
        self._rendered_text = ""
        return self


class JobCardFactory:
    """
    Factory for creating job card pairs for conjoint experiments.
    Uses Strategy pattern for different randomization approaches.
    """
    
    def __init__(self, randomization_strategy=None):
        from app.patterns.strategy import SeededRandomStrategy
        self._strategy = randomization_strategy or SeededRandomStrategy()
        self._builder = JobCardBuilder()
        self._attribute_definitions = None
    
    def set_strategy(self, strategy) -> 'JobCardFactory':
        """Set randomization strategy (Strategy pattern)."""
        self._strategy = strategy
        return self
    
    def _load_attributes(self) -> List[JobAttribute]:
        """
        Lazy load attribute definitions via AttributeService.
        Ensures initialization and provides clear error on failure.
        """
        if self._attribute_definitions is None:
            # Use AttributeService which handles initialization
            self._attribute_definitions = AttributeService.get_all_attributes()
        return self._attribute_definitions
    
    def create_card_pair(self, session_id: ObjectId, round_number: int,
                         session_seed: str) -> Tuple[GeneratedJobCard, GeneratedJobCard]:
        """
        Create a pair of job cards (A and B) for a conjoint round.
        
        Args:
            session_id: The session ObjectId
            round_number: The current round number
            session_seed: Seed for deterministic randomization
        
        Returns:
            Tuple of (card_a, card_b)
        """
        attributes = self._load_attributes()
        
        # Generate attribute combinations using strategy
        attrs_a, attrs_b = self._strategy.generate_pair(
            attributes, round_number, session_seed
        )
        
        # Build Card A
        self._builder.reset()
        card_a = (self._builder
                  .set_attributes(attrs_a)
                  .build_rendered_text(attributes)
                  .build(session_id, 'A', round_number))
        
        # Build Card B
        self._builder.reset()
        card_b = (self._builder
                  .set_attributes(attrs_b)
                  .build_rendered_text(attributes)
                  .build(session_id, 'B', round_number))
        
        return card_a, card_b
    
    def create_and_save_card_pair(self, session_id: ObjectId, round_number: int,
                                   session_seed: str) -> Tuple[GeneratedJobCard, GeneratedJobCard]:
        """Create and persist a card pair."""
        card_a, card_b = self.create_card_pair(session_id, round_number, session_seed)
        card_a.save()
        card_b.save()
        return card_a, card_b
    
    def render_card_html(self, card: GeneratedJobCard) -> str:
        """
        Render a job card as HTML for display.
        """
        attributes = self._load_attributes()
        
        html_parts = ['<div class="job-card-content">']
        
        for attr_def in attributes:
            if attr_def.attribute_key in card.attributes:
                level_id = card.attributes[attr_def.attribute_key]
                display_text = attr_def.get_level_text(level_id)
                
                html_parts.append(f'''
                    <div class="job-attribute">
                        <span class="attribute-label">{attr_def.display_name}:</span>
                        <span class="attribute-value">{display_text}</span>
                    </div>
                ''')
        
        html_parts.append('</div>')
        return ''.join(html_parts)


class AbstractJobCardFactory(ABC):
    """
    Abstract Factory for different types of job card experiments.
    Allows creating families of related objects.
    """
    
    @abstractmethod
    def create_card_pair(self, session_id: ObjectId, round_number: int,
                         session_seed: str) -> Tuple[GeneratedJobCard, GeneratedJobCard]:
        """Create a pair of job cards."""
        pass
    
    @abstractmethod
    def get_attribute_count(self) -> int:
        """Get number of attributes in cards."""
        pass


class StandardJobCardFactory(AbstractJobCardFactory):
    """Standard 6-attribute job card factory."""
    
    def __init__(self):
        self._factory = JobCardFactory()
    
    def create_card_pair(self, session_id: ObjectId, round_number: int,
                         session_seed: str) -> Tuple[GeneratedJobCard, GeneratedJobCard]:
        return self._factory.create_card_pair(session_id, round_number, session_seed)
    
    def get_attribute_count(self) -> int:
        return 6


class SimplifiedJobCardFactory(AbstractJobCardFactory):
    """
    Simplified 3-attribute job card factory.
    For shorter experiments.
    """
    
    CORE_ATTRIBUTES = ['salary', 'work_arrangement', 'benefits']
    
    def __init__(self):
        from app.patterns.strategy import SeededRandomStrategy
        self._strategy = SeededRandomStrategy()
        self._builder = JobCardBuilder()
    
    def create_card_pair(self, session_id: ObjectId, round_number: int,
                         session_seed: str) -> Tuple[GeneratedJobCard, GeneratedJobCard]:
        all_attributes = JobAttribute.get_all_attributes()
        # Filter to core attributes only
        attributes = [a for a in all_attributes 
                      if a.attribute_key in self.CORE_ATTRIBUTES]
        
        attrs_a, attrs_b = self._strategy.generate_pair(
            attributes, round_number, session_seed
        )
        
        self._builder.reset()
        card_a = (self._builder
                  .set_attributes(attrs_a)
                  .build_rendered_text(attributes)
                  .build(session_id, 'A', round_number))
        
        self._builder.reset()
        card_b = (self._builder
                  .set_attributes(attrs_b)
                  .build_rendered_text(attributes)
                  .build(session_id, 'B', round_number))
        
        return card_a, card_b
    
    def get_attribute_count(self) -> int:
        return 3
