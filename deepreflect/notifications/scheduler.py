"""APScheduler integration — schedules the daily notification job."""
from __future__ import annotations

import logging

from deepreflect.config import Config

log = logging.getLogger(__name__)


def setup_notification_jobs(scheduler, cfg: Config) -> None:
    """Register (or remove) the daily notification cron job on *scheduler*."""
    from apscheduler.triggers.cron import CronTrigger
    from deepreflect.notifications.dispatcher import dispatch_notification

    job_id = "daily_notification"

    # Remove any existing job so settings changes take effect immediately
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    if not cfg.notify_enabled or not cfg.notify_channels:
        log.info("Notifications disabled — no job scheduled.")
        return

    try:
        hour, minute = (int(x) for x in cfg.notify_time.split(":"))
    except ValueError:
        log.error("Invalid notify_time '%s' — expected HH:MM.", cfg.notify_time)
        return

    scheduler.add_job(
        dispatch_notification,
        CronTrigger(hour=hour, minute=minute),
        args=[cfg],
        id=job_id,
        replace_existing=True,
    )
    log.info("Daily notification scheduled at %02d:%02d for channels: %s",
             hour, minute, cfg.notify_channels)
