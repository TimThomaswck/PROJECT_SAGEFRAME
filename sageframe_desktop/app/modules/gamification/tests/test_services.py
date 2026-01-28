from app.modules.gamification.services import GamificationService


def test_get_or_create_progress_creates_default_record():
    service = GamificationService()
    try:
        progress = service.get_or_create_progress(user_id=1)
        assert progress.user_id == 1
        assert progress.current_level >= 1
        assert progress.current_xp >= 0
    finally:
        service.close()


def test_award_xp_for_task_increments_xp_and_level():
    service = GamificationService()
    try:
        progress_before = service.get_or_create_progress(user_id=1)
        old_xp = progress_before.current_xp
        old_level = progress_before.current_level
        xp_awarded, leveled_up, prev_level, new_level = service.award_xp_for_task(complexity="moderate", user_id=1)
        assert xp_awarded > 0
        progress_after = service.get_or_create_progress(user_id=1)
        assert progress_after.current_xp >= old_xp + xp_awarded
        if leveled_up:
            assert new_level > old_level
    finally:
        service.close()
