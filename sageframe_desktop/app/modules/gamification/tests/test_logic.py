from app.modules.gamification.logic import XPCalculator, LevelSystem, TaskComplexity


def test_xp_calculation_defaults_to_moderate_when_invalid():
    expected = int(XPCalculator.BASE_XP * XPCalculator.COMPLEXITY_MULTIPLIERS[TaskComplexity.MODERATE])
    assert XPCalculator.calculate_xp("invalid") == expected


def test_xp_calculation_moderate():
    xp = XPCalculator.calculate_xp("moderate")
    expected = int(XPCalculator.BASE_XP * XPCalculator.COMPLEXITY_MULTIPLIERS[TaskComplexity.MODERATE])
    assert xp == expected


def test_level_system_xp_thresholds_monotonic():
    last = 0
    for level in range(2, 10):
        xp = LevelSystem.xp_required_for_level(level)
        assert xp > last
        last = xp


def test_level_system_level_from_xp_progression():
    level1 = LevelSystem.calculate_level_from_xp(0)[0]
    level2 = LevelSystem.calculate_level_from_xp(LevelSystem.BASE_XP_FOR_LEVEL_2)[0]
    level3 = LevelSystem.calculate_level_from_xp(LevelSystem.xp_required_for_level(3))[0]
    assert level1 == 1
    assert level2 >= 2
    assert level3 >= 3


def test_level_up_detection():
    old_xp = 0
    new_xp = LevelSystem.BASE_XP_FOR_LEVEL_2 + 10
    leveled_up, old_level, new_level = LevelSystem.check_level_up(old_xp, new_xp)
    assert leveled_up is True
    assert new_level > old_level
