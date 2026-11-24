# Rate Limiter (Redis + FastAPI)
Sliding window log limiter. Redis sorted set per client and route, Lua script for atomic check.

    pip install -r requirements.txt
    docker run -p 6379:6379 redis
    uvicorn app:app --reload
    for i in $(seq 7); do curl -si localhost:8000/ping | head -1; done   # 5x 200 then 429
    pytest

Env: RL_LIMIT (5), RL_WINDOW_MS (10000), REDIS_URL, RL_FAIL_OPEN (true).
