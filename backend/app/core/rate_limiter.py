import hashlib
import time
from fastapi import Request, HTTPException, status
import redis.asyncio as redis

class RateLimiter:
    """
    Abuse Prevention Engine:
    - Redis-backed sliding window rate limiter
    - Content-hash deduplication to prevent flooding of identical reports
    """

    @staticmethod
    def get_client_identifier(request: Request) -> str:
        # Check forwarded headers first (for proxies/gateways)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown_ip"
        
        # Optionally incorporate device fingerprint header if provided
        device_id = request.headers.get("X-Device-Fingerprint", "")
        if device_id:
            return f"{ip}:{device_id[:16]}"
        return ip

    @classmethod
    async def check_sliding_window(
        cls,
        redis_client: redis.Redis,
        key_prefix: str,
        identifier: str,
        max_requests: int,
        window_seconds: int
    ) -> None:
        if redis_client is None:
            return  # Fail open if redis unavailable

        now = time.time()
        clear_before = now - window_seconds
        key = f"rate_limit:{key_prefix}:{identifier}"

        try:
            # Pipeline: remove old entries, count remaining, add current, set TTL
            pipe = redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, clear_before)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, window_seconds + 10)
            results = await pipe.execute()

            current_count = results[1]
            if current_count >= max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Maximum {max_requests} submissions allowed every {window_seconds // 60} minutes. Please try again later."
                )
        except HTTPException:
            raise
        except Exception:
            # Fail open gracefully if Redis error occurs
            return

    @classmethod
    async def check_content_duplicate(
        cls,
        redis_client: redis.Redis,
        content: str,
        category: str,
        ttl_seconds: int = 900
    ) -> None:
        if redis_client is None:
            return

        normalized = f"{category.strip().lower()}:{content.strip().lower()}"
        content_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        key = f"report_dedup:{content_hash}"

        try:
            is_duplicate = await redis_client.exists(key)
            if is_duplicate:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Duplicate report submission detected within 15 minutes. Our safety team is already processing your earlier report."
                )
            # Store hash for deduplication
            await redis_client.set(key, "1", ex=ttl_seconds)
        except HTTPException:
            raise
        except Exception:
            return

async def check_anonymous_report_rate_limit(
    request: Request,
    redis_client: redis.Redis,
    content: str,
    category: str
) -> None:
    client_id = RateLimiter.get_client_identifier(request)

    # 1. Burst limit: max 2 reports per 60 seconds
    await RateLimiter.check_sliding_window(
        redis_client=redis_client,
        key_prefix="anon_report_burst",
        identifier=client_id,
        max_requests=2,
        window_seconds=60
    )

    # 2. Hourly limit: max 5 reports per hour
    await RateLimiter.check_sliding_window(
        redis_client=redis_client,
        key_prefix="anon_report_hourly",
        identifier=client_id,
        max_requests=5,
        window_seconds=3600
    )

    # 3. Content deduplication: no exact duplicates within 15 mins
    await RateLimiter.check_content_duplicate(
        redis_client=redis_client,
        content=content,
        category=category,
        ttl_seconds=900
    )

async def check_sos_rate_limit(
    request: Request,
    redis_client: redis.Redis
) -> None:
    client_id = RateLimiter.get_client_identifier(request)

    # SOS burst limit: max 5 per 30 seconds (allows rapid panic presses, blocks malicious DOS scripts)
    await RateLimiter.check_sliding_window(
        redis_client=redis_client,
        key_prefix="sos_trigger",
        identifier=client_id,
        max_requests=5,
        window_seconds=30
    )
