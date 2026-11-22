"""Test-wide configuration.

Runs before any test module imports the application, so settings are
built with these values.
"""

import os

# FastAPI's TestClient sends "Host: testserver"; allow it in tests only.
os.environ["LOC_SERVER_ALLOWED_HOSTS"] = "localhost,127.0.0.1,testserver"
