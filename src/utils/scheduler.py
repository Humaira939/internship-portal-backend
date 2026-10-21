"""APScheduler setup: runs the license expiry check every night at 00:00 (Asia/Karachi)."""
from apscheduler.schedulers.background import BackgroundScheduler
 
from src.license_expiry.config import CHECK_ON_STARTUP, TIMEZONE
from src.license_expiry.service import run_license_expiry_check
 
scheduler = BackgroundScheduler(timezone=TIMEZONE)
 
 
def _license_job():
    # Never let an error kill the scheduler thread
    try:
        summary = run_license_expiry_check()
        print(
            "License expiry check finished: "
            f"checked={summary['checked']} sent={summary['sent']} skipped={summary['skipped']} "
            f"frozen={summary['frozen']} failed={summary['failed']}"
        )
    except Exception as error:
        print(f"License expiry check crashed: {error}")
 
 
def start_scheduler():
    if scheduler.running:
        return
 
    # Every night at 00:00. coalesce + misfire_grace_time: if the server was busy or down for a
    # short time, the missed run still happens once instead of being lost.
    scheduler.add_job(
        _license_job,
        "cron",
        hour=0,
        minute=0,
        id="license_expiry_check",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=3600,
    )
 
    # Catch-up: one run right after the server starts (safe, the reminder log prevents duplicates)
    if CHECK_ON_STARTUP:
        scheduler.add_job(_license_job, id="license_expiry_startup_check", replace_existing=True)
 
    scheduler.start()
    print(f"Scheduler started: license expiry check runs daily at 00:00 ({TIMEZONE})")
 
 
def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
 