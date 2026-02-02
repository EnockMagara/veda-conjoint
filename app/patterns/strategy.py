"""
Strategy Pattern Implementation
Different randomization strategies for conjoint experiment design
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
import random
import hashlib
from itertools import product


class RandomizationStrategy(ABC):
    """
    Abstract strategy for generating job attribute combinations.
    Implements Strategy pattern for interchangeable randomization algorithms.
    """
    
    @abstractmethod
    def generate_pair(self, attributes: List, round_number: int,
                      session_seed: str) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        Generate a pair of attribute combinations for A/B comparison.
        
        Args:
            attributes: List of JobAttribute objects
            round_number: Current round number
            session_seed: Seed for reproducibility
        
        Returns:
            Tuple of (attributes_a, attributes_b) dictionaries
        """
        pass
    
    def _create_seeded_random(self, session_seed: str, round_number: int) -> random.Random:
        """Create a seeded random generator for reproducibility."""
        # Combine seed with round for unique but reproducible randomization
        combined_seed = f"{session_seed}_{round_number}"
        seed_hash = int(hashlib.sha256(combined_seed.encode()).hexdigest(), 16) % (2**32)
        return random.Random(seed_hash)


class SeededRandomStrategy(RandomizationStrategy):
    """
    Basic seeded random strategy.
    Randomly selects levels for each attribute with deterministic seed.
    """
    
    def generate_pair(self, attributes: List, round_number: int,
                      session_seed: str) -> Tuple[Dict[str, str], Dict[str, str]]:
        rng = self._create_seeded_random(session_seed, round_number)
        
        attrs_a = {}
        attrs_b = {}
        
        for attr in attributes:
            levels = [level['level_id'] for level in attr.levels]
            
            # Random selection for card A
            attrs_a[attr.attribute_key] = rng.choice(levels)
            
            # Random selection for card B
            attrs_b[attr.attribute_key] = rng.choice(levels)
        
        return attrs_a, attrs_b


class BalancedRandomStrategy(RandomizationStrategy):
    """
    Balanced randomization ensuring cards differ on at least some attributes.
    Prevents identical or nearly identical card pairs.
    """
    
    def __init__(self, min_differences: int = 2):
        self.min_differences = min_differences
    
    def generate_pair(self, attributes: List, round_number: int,
                      session_seed: str) -> Tuple[Dict[str, str], Dict[str, str]]:
        rng = self._create_seeded_random(session_seed, round_number)
        
        attrs_a = {}
        attrs_b = {}
        
        # First pass: random selection for card A
        for attr in attributes:
            levels = [level['level_id'] for level in attr.levels]
            attrs_a[attr.attribute_key] = rng.choice(levels)
        
        # Second pass: ensure minimum differences for card B
        attr_keys = list(attrs_a.keys())
        rng.shuffle(attr_keys)
        
        # Select attributes that must differ
        differ_attrs = set(attr_keys[:self.min_differences])
        
        for attr in attributes:
            levels = [level['level_id'] for level in attr.levels]
            
            if attr.attribute_key in differ_attrs:
                # Must be different from A
                other_levels = [l for l in levels if l != attrs_a[attr.attribute_key]]
                if other_levels:
                    attrs_b[attr.attribute_key] = rng.choice(other_levels)
                else:
                    attrs_b[attr.attribute_key] = rng.choice(levels)
            else:
                # Random selection
                attrs_b[attr.attribute_key] = rng.choice(levels)
        
        return attrs_a, attrs_b


class FullFactorialStrategy(RandomizationStrategy):
    """
    Full factorial design strategy.
    Pre-generates all possible combinations and selects pairs systematically.
    Useful for smaller attribute spaces or when complete coverage is needed.
    """
    
    def __init__(self):
        self._combinations_cache = {}
    
    def _generate_all_combinations(self, attributes: List) -> List[Dict[str, str]]:
        """Generate all possible attribute combinations."""
        cache_key = tuple(attr.attribute_key for attr in attributes)
        
        if cache_key in self._combinations_cache:
            return self._combinations_cache[cache_key]
        
        # Get all levels for each attribute
        all_levels = []
        attr_keys = []
        
        for attr in attributes:
            attr_keys.append(attr.attribute_key)
            all_levels.append([level['level_id'] for level in attr.levels])
        
        # Generate Cartesian product
        combinations = []
        for combo in product(*all_levels):
            combinations.append(dict(zip(attr_keys, combo)))
        
        self._combinations_cache[cache_key] = combinations
        return combinations
    
    def generate_pair(self, attributes: List, round_number: int,
                      session_seed: str) -> Tuple[Dict[str, str], Dict[str, str]]:
        combinations = self._generate_all_combinations(attributes)
        rng = self._create_seeded_random(session_seed, round_number)
        
        # Select two different combinations
        n = len(combinations)
        idx_a = rng.randint(0, n - 1)
        idx_b = rng.randint(0, n - 1)
        
        # Ensure they're different
        attempts = 0
        while idx_b == idx_a and attempts < 100:
            idx_b = rng.randint(0, n - 1)
            attempts += 1
        
        return combinations[idx_a].copy(), combinations[idx_b].copy()


class ConstrainedRandomStrategy(RandomizationStrategy):
    """
    Constrained randomization with level restrictions.
    Allows setting constraints like "if remote, commute_time must be N/A".
    """
    
    def __init__(self, constraints: List[Dict] = None):
        """
        Args:
            constraints: List of constraint rules
                [{'if': {'attr': 'val'}, 'then': {'attr': 'val'}}, ...]
        """
        self.constraints = constraints or []
    
    def _apply_constraints(self, attrs: Dict[str, str]) -> Dict[str, str]:
        """Apply constraint rules to attributes."""
        result = attrs.copy()
        
        for constraint in self.constraints:
            if_condition = constraint.get('if', {})
            then_action = constraint.get('then', {})
            
            # Check if condition is met
            condition_met = all(
                result.get(attr) == val 
                for attr, val in if_condition.items()
            )
            
            if condition_met:
                result.update(then_action)
        
        return result
    
    def generate_pair(self, attributes: List, round_number: int,
                      session_seed: str) -> Tuple[Dict[str, str], Dict[str, str]]:
        rng = self._create_seeded_random(session_seed, round_number)
        
        attrs_a = {}
        attrs_b = {}
        
        for attr in attributes:
            levels = [level['level_id'] for level in attr.levels]
            attrs_a[attr.attribute_key] = rng.choice(levels)
            attrs_b[attr.attribute_key] = rng.choice(levels)
        
        # Apply constraints
        attrs_a = self._apply_constraints(attrs_a)
        attrs_b = self._apply_constraints(attrs_b)
        
        return attrs_a, attrs_b


class DOptimalStrategy(RandomizationStrategy):
    """
    D-optimal experimental design strategy.
    Maximizes information gain by selecting pairs that provide 
    maximum statistical efficiency.
    
    Simplified implementation using variance maximization heuristic.
    """
    
    def __init__(self, history: List[Tuple[Dict, Dict]] = None):
        self.history = history or []
    
    def _calculate_diversity_score(self, attrs: Dict[str, str], 
                                    history: List[Dict]) -> float:
        """Calculate how different this combination is from history."""
        if not history:
            return 1.0
        
        scores = []
        for hist_attrs in history:
            # Count matching attributes
            matches = sum(1 for k, v in attrs.items() 
                         if hist_attrs.get(k) == v)
            scores.append(1 - (matches / len(attrs)))
        
        return sum(scores) / len(scores)
    
    def generate_pair(self, attributes: List, round_number: int,
                      session_seed: str) -> Tuple[Dict[str, str], Dict[str, str]]:
        rng = self._create_seeded_random(session_seed, round_number)
        
        # Generate multiple candidates and pick most diverse
        best_pair = None
        best_score = -1
        
        for _ in range(10):  # Generate 10 candidates
            attrs_a = {}
            attrs_b = {}
            
            for attr in attributes:
                levels = [level['level_id'] for level in attr.levels]
                attrs_a[attr.attribute_key] = rng.choice(levels)
                attrs_b[attr.attribute_key] = rng.choice(levels)
            
            # Calculate combined diversity score
            flat_history = [a for pair in self.history for a in pair]
            score_a = self._calculate_diversity_score(attrs_a, flat_history)
            score_b = self._calculate_diversity_score(attrs_b, flat_history)
            combined_score = score_a + score_b
            
            if combined_score > best_score:
                best_score = combined_score
                best_pair = (attrs_a, attrs_b)
        
        if best_pair:
            self.history.append(best_pair)
            return best_pair
        
        # Fallback to basic random
        attrs_a = {}
        attrs_b = {}
        for attr in attributes:
            levels = [level['level_id'] for level in attr.levels]
            attrs_a[attr.attribute_key] = rng.choice(levels)
            attrs_b[attr.attribute_key] = rng.choice(levels)
        
        return attrs_a, attrs_b
