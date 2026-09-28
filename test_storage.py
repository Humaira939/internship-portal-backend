from src.utils.supabase_storage import supabase
from src.utils.settings import settings

print(supabase.storage.from_(settings.RESUME_BUCKET).list())
print(supabase.storage.from_(settings.TRADE_LICENSE_BUCKET).list())