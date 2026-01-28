"""Gamification logic for XP calculation and leveling system.

This module contains the core game mechanics for progression tracking.
"""

from enum import Enum
from typing import Dict, Tuple


class TaskComplexity(str, Enum):
    """Task complexity levels (matching task model)."""
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class XPCalculator:
    """Calculate XP rewards for task completion based on task properties."""
    
    # Base XP awarded for any task completion
    BASE_XP = 10
    
    # Complexity multipliers for XP calculation
    COMPLEXITY_MULTIPLIERS = {
        TaskComplexity.TRIVIAL: 0.5,
        TaskComplexity.SIMPLE: 1.0,
        TaskComplexity.MODERATE: 1.5,
        TaskComplexity.COMPLEX: 2.5,
        TaskComplexity.VERY_COMPLEX: 4.0,
    }
    
    @classmethod
    def calculate_xp(cls, complexity: str) -> int:
        """Calculate XP for completing a task.
        
        Formula: XP = BASE_XP * complexity_multiplier
        
        Args:
            complexity: Task complexity level as string
            
        Returns:
            XP amount to award (integer)
        """
        try:
            complexity_enum = TaskComplexity(complexity.lower())
        except (ValueError, AttributeError):
            # Default to MODERATE if complexity is invalid
            complexity_enum = TaskComplexity.MODERATE
        
        multiplier = cls.COMPLEXITY_MULTIPLIERS.get(complexity_enum, 1.0)
        return int(cls.BASE_XP * multiplier)


class LevelSystem:
    """Manage user leveling progression and XP thresholds.
    
    Implements an exponential leveling curve where each level requires
    progressively more XP to achieve.
    """
    
    # Starting XP requirement for level 2
    BASE_XP_FOR_LEVEL_2 = 100
    
    # Growth factor for exponential curve (1.2 = 20% increase per level)
    LEVEL_GROWTH_FACTOR = 1.2
    
    # Maximum level (for UI purposes)
    MAX_LEVEL = 100
    
    @classmethod
    def xp_required_for_level(cls, target_level: int) -> int:
        """Calculate total XP required to reach a specific level.
        
        Uses exponential formula:
        Level 1: 0 XP
        Level 2: 100 XP
        Level 3: 100 * 1.2 = 120 XP (total: 220)
        Level 4: 120 * 1.2 = 144 XP (total: 364)
        ...
        
        Args:
            target_level: The level to calculate XP requirement for
            
        Returns:
            Total XP needed from level 1 to reach target_level
        """
        if target_level <= 1:
            return 0
        
        total_xp = 0
        for level in range(2, target_level + 1):
            xp_for_this_level = cls._xp_for_single_level(level)
            total_xp += xp_for_this_level
        
        return total_xp
    
    @classmethod
    def _xp_for_single_level(cls, level: int) -> int:
        """Calculate XP required for a single level transition.
        
        Args:
            level: The level number (2+)
            
        Returns:
            XP required to go from (level-1) to level
        """
        if level <= 1:
            return 0
        
        # Exponential growth: base * (growth_factor ^ (level - 2))
        exponent = level - 2
        xp_needed = cls.BASE_XP_FOR_LEVEL_2 * (cls.LEVEL_GROWTH_FACTOR ** exponent)
        return int(xp_needed)
    
    @classmethod
    def calculate_level_from_xp(cls, current_xp: int) -> Tuple[int, int, int]:
        """Determine user's level based on current XP.
        
        Args:
            current_xp: User's total accumulated XP
            
        Returns:
            Tuple of (current_level, xp_for_current_level, xp_for_next_level)
            - current_level: The level the user is currently at
            - xp_for_current_level: XP user has earned toward current level
            - xp_for_next_level: Total XP needed to reach next level
        """
        if current_xp < 0:
            return (1, 0, cls.xp_required_for_level(2))
        
        # Find the appropriate level
        level = 1
        cumulative_xp = 0
        
        for check_level in range(2, cls.MAX_LEVEL + 1):
            xp_for_level = cls.xp_required_for_level(check_level)
            if current_xp >= xp_for_level:
                level = check_level
                cumulative_xp = xp_for_level
            else:
                break
        
        # Calculate progress within current level
        xp_for_current_level = current_xp - cumulative_xp
        
        # Calculate XP needed for next level
        next_level_total_xp = cls.xp_required_for_level(level + 1)
        xp_for_next_level = next_level_total_xp - cumulative_xp
        
        return (level, xp_for_current_level, xp_for_next_level)
    
    @classmethod
    def check_level_up(cls, old_xp: int, new_xp: int) -> Tuple[bool, int, int]:
        """Check if adding XP causes a level up.
        
        Args:
            old_xp: Previous XP total
            new_xp: New XP total after award
            
        Returns:
            Tuple of (leveled_up, old_level, new_level)
        """
        old_level, _, _ = cls.calculate_level_from_xp(old_xp)
        new_level, _, _ = cls.calculate_level_from_xp(new_xp)
        
        return (new_level > old_level, old_level, new_level)
