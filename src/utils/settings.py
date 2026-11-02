from pydantic_settings import BaseSettings, SettingsConfigDict
 
 
class Settings(BaseSettings):
    DB_CONNECTION: str
    SECRET_KEY: str
 
    # Supabase Storage (for resume and trade license files)
    SUPABASE_URL: str
    SUPABASE_SECRET_KEY: str
    RESUME_BUCKET: str
    TRADE_LICENSE_BUCKET: str
 
    # Forgot / Reset password
    EMAIL_ADDRESS: str
    EMAIL_APP_PASSWORD: str
    FRONTEND_RESET_URL: str
 
    # License expiry reminders (these have default values, so nothing new is needed in .env)
    LICENSE_TIMEZONE: str = "Asia/Karachi"          # one timezone for "today" everywhere
    GRACE_PERIOD_DAYS: int = 28                     # days after expiry before the account is frozen
    FRONTEND_UPLOAD_URL: str = "http://127.0.0.1:8000/company-profile"  # button link in reminder emails
    LICENSE_CHECK_ON_STARTUP: bool = True           # run one check when the server starts (catch-up)
 
    # Contact Us form (landing page)
    SUPPORT_EMAIL: str = ""                         # where contact messages are sent; empty = EMAIL_ADDRESS
    CONTACT_MAX_PER_IP_PER_HOUR: int = 5            # spam protection: messages from one IP in one hour
    CONTACT_MAX_PER_EMAIL_PER_HOUR: int = 3         # spam protection: messages from one email in one hour
 
    # Frontend pages served by this backend (clean URLs: /login, not login.html)
    FRONTEND_DIR: str = "../SmartIntern-fyp/internship-portal-frontend"   # folder that contains html, css, js, images
    FRONTEND_BASE_URL: str = "http://127.0.0.1:8000"                      # used for the links inside emails
 
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
 
 
settings = Settings()
 
 