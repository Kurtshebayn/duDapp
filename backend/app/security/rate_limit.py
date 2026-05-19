"""
Rate limiting module for duDapp.

Uses slowapi with get_ipaddr (X-Forwarded-For-aware) as the key function.
get_ipaddr is required instead of get_remote_address because Render terminates
TLS at a proxy — get_remote_address would coalesce all clients into the proxy IP.
"""
from slowapi import Limiter
from slowapi.util import get_ipaddr

# Module-level Limiter instance — single source of truth.
# default_limits=[] means no global limit; per-route limits are applied via decorators.
# Tests disable this via limiter.enabled = False (see conftest.py disable_rate_limit fixture).
limiter = Limiter(key_func=get_ipaddr, default_limits=[])
