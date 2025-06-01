"""
Proxy configuration for YouTube transcript extraction.
Proxy credentials should be set as environment variables.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get proxy configuration from environment variables
PROXY_USERNAME = os.getenv('PROXY_USERNAME')
PROXY_PASSWORD = os.getenv('PROXY_PASSWORD')
PROXY_HOST = os.getenv('PROXY_HOST')
PROXY_PORT = os.getenv('PROXY_PORT')

# Construct proxy URL if credentials are available
PROXY_LIST = []
if all([PROXY_USERNAME, PROXY_PASSWORD, PROXY_HOST, PROXY_PORT]):
    proxy_url = f"http://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}"
    PROXY_LIST.append(proxy_url)

# Proxy rotation settings
PROXY_ROTATION_ENABLED = True
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds 