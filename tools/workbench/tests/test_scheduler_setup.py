import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from app import app, get_scheduler


@pytest.fixture(scope="session", autouse=True)
def _verify_url():
    yield


def test_scheduler_has_sermon_sync_job():
    scheduler = get_scheduler()
    job_ids = {j.id for j in scheduler.get_jobs()}
    assert 'sermon_sync_cron' in job_ids


def test_scheduler_job_runs_every_4_hours():
    scheduler = get_scheduler()
    job = scheduler.get_job('sermon_sync_cron')
    assert job is not None
    trigger_str = str(job.trigger)
    assert '4' in trigger_str or '14400' in trigger_str
