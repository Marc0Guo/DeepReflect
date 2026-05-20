"""API routes for notification management."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from deepreflect.config import load_config, save_config
from deepreflect.notifications.dispatcher import dispatch_notification, get_last_sent

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/status")
async def status(request: Request):
    """Return scheduler status and last sent timestamp."""
    cfg = load_config()
    scheduler = getattr(request.app.state, "scheduler", None)
    next_fire = None
    if scheduler:
        job = scheduler.get_job("daily_notification")
        if job and job.next_run_time:
            next_fire = job.next_run_time.isoformat()

    last = get_last_sent()
    return {
        "enabled": cfg.notify_enabled,
        "notify_time": cfg.notify_time,
        "channels": cfg.notify_channels,
        "next_fire_time": next_fire,
        "last_sent": last.isoformat() if last else None,
    }


@router.post("/send-now")
async def send_now():
    """Immediately dispatch to all configured channels."""
    cfg = load_config()
    if not cfg.notify_channels:
        raise HTTPException(status_code=400, detail="No channels configured.")
    if not cfg.llm_api_key and cfg.llm_provider != "ollama":
        raise HTTPException(status_code=400, detail="LLM API key not configured.")
    results = await dispatch_notification(cfg)
    return {"results": results}


@router.post("/test/{platform}")
async def test_platform(platform: str):
    """Send a test notification to a single platform using current config."""
    cfg = load_config()
    if not cfg.llm_api_key and cfg.llm_provider != "ollama":
        raise HTTPException(status_code=400, detail="LLM API key not configured.")

    valid = {"discord", "slack", "imessage", "wechat"}
    if platform not in valid:
        raise HTTPException(status_code=400, detail=f"Unknown platform. Choose from: {valid}")

    # Temporarily restrict channels to just this one
    from deepreflect.config import Config
    test_cfg = cfg.model_copy(update={"notify_channels": [platform]})
    results = await dispatch_notification(test_cfg)
    return {"platform": platform, "result": results.get(platform, "no result")}


@router.post("/reload-schedule")
async def reload_schedule(request: Request):
    """Re-register the scheduler job after settings change."""
    scheduler = getattr(request.app.state, "scheduler", None)
    if scheduler is None:
        raise HTTPException(status_code=503, detail="Scheduler not running.")
    cfg = load_config()
    from deepreflect.notifications.scheduler import setup_notification_jobs
    setup_notification_jobs(scheduler, cfg)
    return {"ok": True, "enabled": cfg.notify_enabled, "time": cfg.notify_time}
