"""Run / test the license expiry check by hand (testing and the demo).
 
Run it from the project root (the folder that contains `src` and `scripts`):
 
  python -m scripts.run_license_check                        run the check for today (real run)
  python -m scripts.run_license_check --dry-run              only show what would happen
  python -m scripts.run_license_check --date 2026-12-01      pretend today is 2026-12-01
  python -m scripts.run_license_check --company-id 4         check only company 4
 
Demo helpers (they change data of ONE company):
  python -m scripts.run_license_check --company-id 4 --set-expiry 2026-10-26   set its license expiry date
  python -m scripts.run_license_check --company-id 4 --reset-log               delete its reminder log rows
 
NOTE: a real run (without --dry-run) really sends emails and really freezes companies.
"""
import argparse
from datetime import date, datetime
 
from src.company.model import CompanyModel
from src.license_expiry.model import LicenseReminderLog
from src.license_expiry.service import run_license_expiry_check
from src.utils.db import get_db
 
 
def parse_date(text: str) -> date:
    return datetime.strptime(text, "%Y-%m-%d").date()
 
 
def main():
    parser = argparse.ArgumentParser(description="SmartIntern license expiry check")
    parser.add_argument("--date", type=parse_date, help="pretend today is this date (YYYY-MM-DD)")
    parser.add_argument("--company-id", type=int, help="check only this company")
    parser.add_argument("--dry-run", action="store_true", help="do not send emails or change anything")
    parser.add_argument("--set-expiry", type=parse_date, help="set the license expiry date of --company-id")
    parser.add_argument("--reset-log", action="store_true", help="delete the reminder log rows of --company-id")
    args = parser.parse_args()
 
    if (args.set_expiry or args.reset_log) and args.company_id is None:
        parser.error("--set-expiry and --reset-log need --company-id")
 
    # ---- demo helpers ----
    if args.set_expiry or args.reset_log:
        generator = get_db()
        db = next(generator)
        try:
            company = db.query(CompanyModel).filter(CompanyModel.id == args.company_id).first()
            if not company:
                parser.error(f"company {args.company_id} not found")
            if args.set_expiry:
                company.license_expiry_date = args.set_expiry
                db.commit()
                print(f"Company {company.id}: license expiry date set to {args.set_expiry}")
            if args.reset_log:
                deleted = (
                    db.query(LicenseReminderLog)
                    .filter(LicenseReminderLog.company_id == company.id)
                    .delete()
                )
                db.commit()
                print(f"Company {company.id}: {deleted} reminder log row(s) deleted")
        finally:
            generator.close()
 
    # ---- the check itself (skipped when only a helper was used) ----
    if args.set_expiry or args.reset_log:
        if not (args.date or args.dry_run):
            return
 
    summary = run_license_expiry_check(
        today=args.date, company_id=args.company_id, dry_run=args.dry_run
    )
 
    print(f"\nLicense check for {summary['date']}{'  (DRY RUN)' if args.dry_run else ''}")
    print(
        f"checked={summary['checked']}  sent={summary['sent']}  skipped={summary['skipped']}  "
        f"frozen={summary['frozen']}  failed={summary['failed']}"
    )
    for item in summary["details"]:
        print(
            f"  company {item['company_id']:>3} | {item['email']:<30} | expiry {item['expiry_date']} "
            f"| days_left {item['days_left']:>4} | {item['milestone']:<6} | {item['action']}"
        )
 
 
if __name__ == "__main__":
    main()
 