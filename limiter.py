"""Sliding window log rate limiter backed by a Redis sorted set (atomic via Lua)."""
import uuid
import redis

LUA = """
local t = redis.call('TIME')
local now = t[1] * 1000 + math.floor(t[2] / 1000)
local window = tonumber(ARGV[1])
local limit = tonumber(ARGV[2])
redis.call('ZREMRANGEBYSCORE', KEYS[1], 0, now - window)
local count = redis.call('ZCARD', KEYS[1])
if count < limit then
  redis.call('ZADD', KEYS[1], now, now .. '-' .. ARGV[3])
  redis.call('PEXPIRE', KEYS[1], window)
  return {1, limit - count - 1, 0}
end
local oldest = redis.call('ZRANGE', KEYS[1], 0, 0, 'WITHSCORES')
return {0, 0, window - (now - tonumber(oldest[2]))}
"""


class RateLimiter:
    def __init__(self, client: redis.Redis, limit: int = 5, window_ms: int = 10_000, prefix: str = "rl"):
        self.limit, self.window_ms, self.prefix = limit, window_ms, prefix
        self._script = client.register_script(LUA)

    def check(self, client_id: str, route: str = "global"):
        """Returns (allowed, remaining, retry_after_ms)."""
        key = f"{self.prefix}:{client_id}:{route}"
        ok, remaining, retry = self._script(
            keys=[key], args=[self.window_ms, self.limit, uuid.uuid4().hex[:8]]
        )
        return bool(ok), int(remaining), int(retry)
