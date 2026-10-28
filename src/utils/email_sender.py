from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from html import escape
from pathlib import Path
import smtplib
 
from src.utils.settings import settings
 
# Logo file: internship_portal/assets/smartintern-logo.png
LOGO_PATH = Path(__file__).resolve().parent.parent.parent / "assets" / "smartintern-logo.png"
 
 
def _login_url() -> str:
    # Built from FRONTEND_RESET_URL: .../html/reset-password.html -> .../html/login.html
    base = settings.FRONTEND_RESET_URL.rsplit("/", 1)[0]
    return f"{base}/login.html"
 
 
def _send_email(to_email: str, subject: str, plain_body: str, html_body: str):
    # "related" lets the HTML refer to an image that is attached inside the same email
    message = MIMEMultipart("related")
    message["From"] = formataddr(("SmartIntern", settings.EMAIL_ADDRESS))
    message["To"] = to_email
    message["Subject"] = subject
 
    # Plain-text and HTML versions of the same message
    alternative = MIMEMultipart("alternative")
    alternative.attach(MIMEText(plain_body, "plain"))
    alternative.attach(MIMEText(html_body, "html"))
    message.attach(alternative)
 
    # Attach the logo; the HTML finds it through its id: <img src="cid:logo">
    if LOGO_PATH.exists():
        with open(LOGO_PATH, "rb") as logo_file:
            logo_image = MIMEImage(logo_file.read())
        logo_image.add_header("Content-ID", "<logo>")
        logo_image.add_header("Content-Disposition", "inline", filename="smartintern-logo.png")
        message.attach(logo_image)
 
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(settings.EMAIL_ADDRESS, settings.EMAIL_APP_PASSWORD)
        server.send_message(message)
 
 
def _html_wrapper(title: str, message_lines: list[str], button_text: str = "", button_link: str = "") -> str:
    paragraphs = "".join(
        f"<p style='margin:0 0 16px;color:#44403f;font-size:15px;line-height:1.7;'>{line}</p>"
        for line in message_lines
    )
 
    button_html = ""
    if button_text and button_link:
        button_html = f"""
        <table cellpadding="0" cellspacing="0" style="margin:26px 0;">
            <tr>
                <td style="border-radius:8px;background:#8d63ad;">
                    <a href="{button_link}"
                       style="display:inline-block;padding:13px 32px;color:#ffffff;
                              text-decoration:none;font-size:14px;font-weight:600;
                              font-family:Arial,Helvetica,sans-serif;">
                        {button_text}
                    </a>
                </td>
            </tr>
        </table>
        """
 
    # Round logo placed next to the "SmartIntern" text (only if the logo file exists)
    logo_cell = ""
    if LOGO_PATH.exists():
        logo_cell = """
        <td style="vertical-align:middle;padding-right:12px;">
            <img src="cid:logo" width="42" height="42" alt=""
                 style="display:block;width:42px;height:42px;border-radius:50%;" />
        </td>
        """
 
    return f"""
    <html>
    <body style="margin:0;padding:0;background:#f4f4f5;font-family:Arial,Helvetica,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f5;padding:40px 0;">
            <tr>
                <td align="center">
                    <table width="520" cellpadding="0" cellspacing="0"
                           style="background:#ffffff;border:1px solid #e5e5e5;border-radius:10px;overflow:hidden;">
 
                        <!-- Header: round logo + SmartIntern text -->
                        <tr>
                            <td style="padding:20px 32px;border-bottom:1px solid #eeeeee;">
                                <table cellpadding="0" cellspacing="0">
                                    <tr>
                                        {logo_cell}
                                        <td style="vertical-align:middle;">
                                            <span style="font-size:20px;font-weight:700;color:#29232b;font-family:Arial,sans-serif;">
                                                Smart<span style="color:#8d63ad;">Intern</span>
                                            </span>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
 
                        <!-- Body -->
                        <tr>
                            <td style="padding:32px;">
                                <h2 style="margin:0 0 18px;color:#29232b;font-size:20px;font-family:Arial,sans-serif;">
                                    {title}
                                </h2>
                                {paragraphs}
                                {button_html}
                            </td>
                        </tr>
 
                        <!-- Footer -->
                        <tr>
                            <td style="padding:18px 32px;background:#fafafa;border-top:1px solid #eeeeee;">
                                <p style="margin:0;color:#999999;font-size:12px;line-height:1.6;font-family:Arial,sans-serif;">
                                    This is an automated message from SmartIntern &mdash; AI-Based Smart Internship
                                    Recommendation Portal. Please do not reply to this email.
                                </p>
                            </td>
                        </tr>
 
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
 
 
# ======================================================================
# PASSWORD RESET
# ======================================================================
def send_reset_email(to_email: str, reset_link: str):
    plain_body = (
        "We received a request to reset your SmartIntern password.\n\n"
        f"Click the link below to set a new password (valid for 15 minutes):\n{reset_link}\n\n"
        "If you did not request this, you can safely ignore this email."
    )
    html_body = _html_wrapper(
        title="Reset your password",
        message_lines=[
            "We received a request to reset your SmartIntern account password.",
            "This link is valid for <b>15 minutes</b>. If you did not request this, you can safely ignore this email.",
        ],
        button_text="Reset Password",
        button_link=reset_link,
    )
    _send_email(to_email, "SmartIntern - Reset your password", plain_body, html_body)
 
 
# ======================================================================
# COMPANY VERIFICATION (sent by the admin's Verify / Reject buttons)
# ======================================================================
def send_company_verified_email(to_email: str, company_name: str):
    plain_body = (
        f"Dear {company_name},\n\n"
        "Your company account has been verified. Welcome to SmartIntern!\n"
        "You can now log in and start posting internships to connect with talented students.\n\n"
        f"Log in here: {_login_url()}"
    )
    html_body = _html_wrapper(
        title="Your account has been verified",
        message_lines=[
            f"Dear {escape(company_name)},",
            "Congratulations! Your company account has been <b>verified</b>. Welcome to SmartIntern!",
            "You can now log in and start posting internships to connect with talented students.",
        ],
        button_text="Log in to SmartIntern",
        button_link=_login_url(),
    )
    _send_email(to_email, "SmartIntern - Your company account has been verified", plain_body, html_body)
 
 
def send_company_rejected_email(to_email: str, company_name: str, reason: str = ""):
    plain_lines = [
        f"Dear {company_name},",
        "",
        "Thank you for registering on SmartIntern. After reviewing the details and the trade license "
        "you submitted, we were unable to verify your company account at this time.",
    ]
    html_lines = [
        f"Dear {escape(company_name)},",
        "Thank you for registering on SmartIntern. After reviewing the details and the trade license "
        "you submitted, we were unable to verify your company account at this time.",
    ]
    if reason:
        plain_lines += ["", f"Reason: {reason}"]
        html_lines.append(f"<b>Reason:</b> {escape(reason)}")
 
    closing = (
        "If you believe this decision was made in error, please get in touch with the "
        "SmartIntern administration."
    )
    plain_lines += ["", closing]
    html_lines.append(closing)
 
    html_body = _html_wrapper(
        title="We could not verify your company",
        message_lines=html_lines,
    )
    _send_email(
        to_email,
        "SmartIntern - Update on your company verification",
        "\n".join(plain_lines),
        html_body,
    )
 
 
# ======================================================================
# TRADE LICENSE REMINDERS (used by the scheduler, later)
# ======================================================================
def send_license_warning_email(to_email: str, company_name: str, expiry_date):
    plain_body = (
        f"Dear {company_name},\n\n"
        f"Your trade license on SmartIntern is set to expire on {expiry_date}.\n"
        "Please renew and upload your updated trade license before it expires. "
        "If it is not renewed in time, you will not be able to post new internships."
    )
    html_body = _html_wrapper(
        title="Your trade license is expiring soon",
        message_lines=[
            f"Dear {escape(company_name)},",
            f"Your trade license on SmartIntern is set to expire on <b>{expiry_date}</b>.",
            "Please renew and upload your updated trade license before it expires to continue posting internships without interruption.",
        ],
    )
    _send_email(to_email, "SmartIntern - Your trade license is expiring soon", plain_body, html_body)
 
 
def send_license_expired_email(to_email: str, company_name: str):
    plain_body = (
        f"Dear {company_name},\n\n"
        "Your trade license on SmartIntern has expired.\n"
        "You will not be able to post new internships until you upload a valid, updated trade license."
    )
    html_body = _html_wrapper(
        title="Your trade license has expired",
        message_lines=[
            f"Dear {escape(company_name)},",
            "Your trade license on SmartIntern has <b>expired</b>.",
            "You will not be able to post new internships until you upload a valid, updated trade license.",
        ],
    )
    _send_email(to_email, "SmartIntern - Your trade license has expired", plain_body, html_body)
 
# ======================================================================
# TRADE LICENSE RE-UPLOAD REQUEST (sent by the admin's "Request re-upload" button)
# ======================================================================
def send_company_reupload_required_email(to_email: str, company_name: str, reason: str = ""):
    reason = reason or "Your trade license could not be verified."
 
    plain_body = (
        f"Dear {company_name},\n\n"
        "While reviewing your SmartIntern company account, we found a problem with your trade license.\n\n"
        f"Reason: {reason}\n\n"
        "Please log in and upload a valid, updated trade license. "
        "Your account will be reviewed again after you upload it. "
        "You will be able to post internships once it is verified.\n\n"
        f"Log in here: {_login_url()}"
    )
    html_body = _html_wrapper(
        title="Please upload your trade license again",
        message_lines=[
            f"Dear {escape(company_name)},",
            "While reviewing your SmartIntern company account, we found a problem with your trade license.",
            f"<b>Reason:</b> {escape(reason)}",
            "Please log in and upload a valid, updated trade license. Your account will be reviewed again "
            "after you upload it, and you will be able to post internships once it is verified.",
        ],
        button_text="Log in to SmartIntern",
        button_link=_login_url(),
    )
    _send_email(
        to_email,
        "SmartIntern - Please upload your trade license again",
        plain_body,
        html_body,
    )
 
 
# ======================================================================
# LICENSE EXPIRY MILESTONE EMAILS (sent by the daily job: license_expiry/service.py)
#   D-7, D-3, D0, +14, +25, FROZEN
# ======================================================================
def _days_text(number: int) -> str:
    return f"{number} day" if number == 1 else f"{number} days"
 
 
def _license_email_content(milestone: str, company_name: str, expiry_date, days_left: int):
    """Returns (subject, title, lines, button_text). The numbers come from the real dates,
    so a catch-up email after server downtime still says the correct number of days."""
    from datetime import timedelta
 
    from src.license_expiry.config import D_MINUS_3, D_MINUS_7, D_ZERO, FROZEN, GRACE_PERIOD_DAYS, PLUS_14, PLUS_25
 
    expiry = expiry_date.strftime("%d %b %Y")
    freeze_date = (expiry_date + timedelta(days=GRACE_PERIOD_DAYS)).strftime("%d %b %Y")
    remaining = max(GRACE_PERIOD_DAYS + days_left, 0)   # days left before the account is frozen
    hello = f"Hello {company_name},"
 
    if milestone == D_MINUS_7:
        return (
            f"Your SmartIntern license expires in {_days_text(days_left)}",
            "Your trade license expires soon",
            [hello,
             f"This is a reminder that your trade license on SmartIntern is set to expire on {expiry}. "
             "Please upload your renewed license before then to keep your account active."],
            "Update my license",
        )
    if milestone == D_MINUS_3:
        return (
            f"Reminder: your license expires in {_days_text(days_left)}",
            "Your trade license expires very soon",
            [hello,
             f"Your license expires on {expiry}, just {_days_text(days_left)} from now. "
             "Please upload the renewed copy as soon as possible so your account is not affected."],
            "Update my license",
        )
    if milestone == D_ZERO:
        expired_text = "Your trade license expired today." if days_left == 0 else f"Your trade license expired on {expiry}."
        return (
            f"Your license has expired: {_days_text(remaining)} to update",
            "Your trade license has expired",
            [hello,
             f"{expired_text} You have {_days_text(remaining)}, until {freeze_date}, to upload a new valid license. "
             "If we do not receive it by then, your account will be frozen and you will not be able to "
             "post or manage internships."],
            "Upload new license",
        )
    if milestone == PLUS_14:
        return (
            f"{_days_text(remaining)} left to update your license",
            "Please update your trade license",
            [hello,
             f"Your license has expired and you have {_days_text(remaining)} remaining before your account "
             f"is frozen on {freeze_date}. Please upload a valid license to avoid losing access."],
            "Upload new license",
        )
    if milestone == PLUS_25:
        return (
            f"Final warning: account freezes in {_days_text(remaining)}",
            "Final warning",
            [hello,
             f"This is a final reminder. Your account will be frozen on {freeze_date} unless you upload a "
             "valid license. Frozen accounts cannot post or manage internships until a license is verified."],
            "Upload new license",
        )
    if milestone == FROZEN:
        return (
            "Your SmartIntern account has been frozen",
            "Your account has been frozen",
            [hello,
             f"We did not receive a valid license within the {GRACE_PERIOD_DAYS}-day grace period, so your "
             "account has been frozen. Upload a valid license and our team will verify it and restore your access."],
            "Upload license to restore access",
        )
    raise ValueError(f"Unknown license milestone: {milestone}")
 
 
def send_license_milestone_email(to_email: str, company_name: str, milestone: str, expiry_date, days_left: int):
    from src.license_expiry.config import FRONTEND_UPLOAD_URL
 
    subject, title, lines, button_text = _license_email_content(milestone, company_name, expiry_date, days_left)
 
    plain_body = "\n\n".join(lines) + f"\n\n{button_text}: {FRONTEND_UPLOAD_URL}"
    html_body = _html_wrapper(
        title=title,
        message_lines=[escape(line) for line in lines],
        button_text=button_text,
        button_link=FRONTEND_UPLOAD_URL,
    )
    _send_email(to_email, f"SmartIntern - {subject}", plain_body, html_body)
 
 
# ======================================================================
# NEW APPLICANT (sent to the company when a student applies to its internship)
# ======================================================================
def send_new_applicant_email(
    to_email: str,
    company_name: str,
    student_name: str,
    internship_title: str,
    university: str = None,
):
    # .../html/reset-password.html -> .../html/view-applicants.html
    applicants_url = settings.FRONTEND_RESET_URL.rsplit("/", 1)[0] + "/view-applicants.html"
 
    who = f"{student_name} ({university})" if university else student_name
    plain_body = (
        f"Hello {company_name},\n\n"
        f"You have a new applicant. {who} has applied for your internship \"{internship_title}\".\n\n"
        f"Review the application here: {applicants_url}"
    )
    html_body = _html_wrapper(
        title="You have a new applicant",
        message_lines=[
            f"Hello {escape(company_name)},",
            f"<b>{escape(who)}</b> has applied for your internship <b>{escape(internship_title)}</b>.",
            "You can review the application and the student's resume on your applicants page.",
        ],
        button_text="View applicants",
        button_link=applicants_url,
    )
    _send_email(to_email, "SmartIntern - New applicant for " + internship_title, plain_body, html_body)
 