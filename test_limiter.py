import time
import fakeredis
from limiter import RateLimiter


def test_blocks_after_limit_and_recovers():
    rl = RateLimiter(fakeredis.FakeRedis(), limit=3, window_ms=500)
    assert [rl.check("u1")[0] for _ in range(4)] == [True, True, True, False]
    assert rl.check("u2")[0] is True          # other clients unaffected
    time.sleep(0.6)
    assert rl.check("u1")[0] is True          # window slid, allowed again
