"""
Course Configurator Service
Determines optimal course structure based on topic complexity and difficulty level.
Pure Python implementation - no AI calls required.
"""
from typing import Literal, NamedTuple
from app.models.course import CourseConfig


class DifficultyPreset(NamedTuple):
    """Preset configuration for a difficulty level."""
    min_chapters: int
    max_chapters: int
    time_per_chapter_minutes: int
    chapter_depth: Literal["overview", "detailed", "comprehensive"]


# Difficulty presets define the range of chapters and depth for each level
DIFFICULTY_PRESETS: dict[str, DifficultyPreset] = {
    "beginner": DifficultyPreset(
        min_chapters=4,
        max_chapters=6,
        time_per_chapter_minutes=25,
        chapter_depth="overview"
    ),
    "intermediate": DifficultyPreset(
        min_chapters=6,
        max_chapters=8,
        time_per_chapter_minutes=45,
        chapter_depth="detailed"
    ),
    "advanced": DifficultyPreset(
        min_chapters=8,
        max_chapters=12,
        time_per_chapter_minutes=90,
        chapter_depth="comprehensive"
    ),
}


class CourseConfigurator:
    """
    Determines optimal course structure based on complexity and difficulty.

    Uses the complexity score from TopicValidator (1-10) combined with
    difficulty presets to calculate recommended chapter count and study time.
    """

    def __init__(self):
        """Initialize the course configurator."""
        self.presets = DIFFICULTY_PRESETS

    def _calculate_chapters_for_complexity(
        self,
        complexity_score: int,
        preset: DifficultyPreset
    ) -> int:
        """
        Calculate recommended chapters based on complexity score.

        Args:
            complexity_score: Topic complexity from 1-10
            preset: Difficulty preset with min/max chapters

        Returns:
            Recommended number of chapters
        """
        # Clamp complexity to valid range
        complexity = max(1, min(10, complexity_score))

        chapter_range = preset.max_chapters - preset.min_chapters

        if complexity <= 3:
            # Low complexity: use minimum chapters
            return preset.min_chapters
        elif complexity <= 6:
            # Medium complexity: use mid-range
            # Map 4-6 to proportional position in range
            progress = (complexity - 3) / 3  # 0.33 to 1.0
            additional = int(chapter_range * progress * 0.5)
            return preset.min_chapters + additional
        else:
            # High complexity (7-10): use upper range to max
            # Map 7-10 to upper half of range
            progress = (complexity - 6) / 4  # 0.25 to 1.0
            additional = int(chapter_range * (0.5 + progress * 0.5))
            return preset.min_chapters + additional

    def get_config(
        self,
        complexity_score: int,
        difficulty: Literal["beginner", "intermediate", "advanced"]
    ) -> CourseConfig:
        """
        Get optimal course configuration based on complexity and difficulty.

        Args:
            complexity_score: Topic complexity score from 1-10 (from TopicValidator)
            difficulty: User-selected difficulty level

        Returns:
            CourseConfig with recommended structure

        Examples:
            >>> configurator = CourseConfigurator()
            >>> config = configurator.get_config(complexity_score=5, difficulty="beginner")
            >>> config.recommended_chapters
            5
            >>> config.chapter_depth
            'overview'
        """
        # Get preset for difficulty level
        preset = self.presets.get(difficulty)
        if not preset:
            # Default to intermediate if invalid difficulty
            preset = self.presets["intermediate"]
            difficulty = "intermediate"

        # Calculate recommended chapters based on complexity
        recommended_chapters = self._calculate_chapters_for_complexity(
            complexity_score,
            preset
        )

        # Calculate total study hours
        total_minutes = recommended_chapters * preset.time_per_chapter_minutes
        estimated_hours = round(total_minutes / 60, 1)

        return CourseConfig(
            recommended_chapters=recommended_chapters,
            estimated_study_hours=estimated_hours,
            time_per_chapter_minutes=preset.time_per_chapter_minutes,
            chapter_depth=preset.chapter_depth,
            difficulty=difficulty
        )

    def get_preset(
        self,
        difficulty: Literal["beginner", "intermediate", "advanced"]
    ) -> DifficultyPreset:
        """
        Get the raw preset for a difficulty level.

        Args:
            difficulty: Difficulty level

        Returns:
            DifficultyPreset with min/max chapters and depth
        """
        return self.presets.get(difficulty, self.presets["intermediate"])

    def get_all_presets(self) -> dict[str, dict]:
        """
        Get all difficulty presets as dictionaries.

        Returns:
            Dictionary of all presets
        """
        return {
            level: {
                "min_chapters": preset.min_chapters,
                "max_chapters": preset.max_chapters,
                "time_per_chapter_minutes": preset.time_per_chapter_minutes,
                "chapter_depth": preset.chapter_depth
            }
            for level, preset in self.presets.items()
        }


# Singleton instance
_configurator_instance: CourseConfigurator | None = None


def get_course_configurator() -> CourseConfigurator:
    """Get or create the CourseConfigurator singleton instance."""
    global _configurator_instance
    if _configurator_instance is None:
        _configurator_instance = CourseConfigurator()
    return _configurator_instance
