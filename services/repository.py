import os

# Read the database deployment profile. Default to local if not explicitly defined.
DATABASE_MODE = os.getenv("DATABASE_MODE", "local").lower()

if DATABASE_MODE == "cloud":
    from .repo_supabase import *
else:
    from .repo_sqlite import *

# PLATFORMS, SCOPES, DEFAULT_PLATFORM, DEFAULT_SCOPE are re-exported via the * import
# so callers can do: from services.repository import PLATFORMS, SCOPES
