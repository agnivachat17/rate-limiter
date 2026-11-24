import math
import os
import redis
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from limiter import RateLimiter

LIMIT = int(os.getenv("RL_LIMIT", 5))
WINDOW_MS = int(os.getenv("RL_WINDOW_MS", 10_000))
FAIL_OPEN = os.getenv("RL_FAIL_OPEN", "true") == "true"

r = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
limiter = RateLimiter(r, LIMIT, WINDOW_MS)
app = FastAPI(title="Rate Limiter Demo")


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    client_id = request.headers.get("X-API-Key") or request.client.host
    try:
        allowed, remaining, retry_ms = limiter.check(client_id, request.url.path)
    except redis.RedisError:
        if FAIL_OPEN:
            return await call_next(request)
        return JSONResponse({"detail": "limiter unavailable"}, status_code=503)

    headers = {"X-RateLimit-Limit": str(LIMIT), "X-RateLimit-Remaining": str(remaining)}
    if not allowed:
        headers["Retry-After"] = str(math.ceil(retry_ms / 1000))
        return JSONResponse({"detail": "Too Many Requests"}, status_code=429, headers=headers)
    response = await call_next(request)
    response.headers.update(headers)
    return response


@app.get("/ping")
def ping():
    return {"message": "pong"}
