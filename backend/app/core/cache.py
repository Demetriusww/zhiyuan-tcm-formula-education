"""可选的 Redis JSON 缓存。

缓存只承担性能优化职责。Redis 未配置、未启动或运行中断时，所有读写都会
安全降级为 no-op，业务接口继续直接访问数据库。
"""
import json
import logging
import time
from typing import Any, Optional

try:
    from redis.asyncio import Redis
    from redis.exceptions import RedisError
except ImportError:  # pragma: no cover - requirements 正常安装时可用
    Redis = None
    RedisError = Exception

from app.core.config import settings


logger = logging.getLogger("tcm_platform.cache")


class CacheManager:
    """异步 Redis 缓存管理器，连接失败时自动熔断。"""

    def __init__(self) -> None:
        self._client: Optional[Redis] = None
        self._disabled_until = 0.0

    @property
    def enabled(self) -> bool:
        return bool(settings.CACHE_ENABLED and Redis is not None)

    async def _get_client(self) -> Optional[Redis]:
        if not self.enabled or time.monotonic() < self._disabled_until:
            return None
        if self._client is None:
            self._client = Redis.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=0.25,
                socket_timeout=0.5,
            )
        return self._client

    def _mark_unavailable(self, exc: Exception) -> None:
        # 避免 Redis 故障时每个请求都重复等待连接超时。
        self._disabled_until = time.monotonic() + 30.0
        logger.warning("Redis 缓存暂不可用，已降级为数据库直连: %s", exc)

    async def get_json(self, key: str) -> Any:
        client = await self._get_client()
        if client is None:
            return None
        try:
            value = await client.get(key)
            return json.loads(value) if value else None
        except (RedisError, json.JSONDecodeError, OSError) as exc:
            self._mark_unavailable(exc)
            return None

    async def set_json(self, key: str, value: Any, ttl: int) -> None:
        client = await self._get_client()
        if client is None:
            return
        try:
            await client.set(key, json.dumps(value, ensure_ascii=False), ex=ttl)
        except (RedisError, TypeError, ValueError, OSError) as exc:
            self._mark_unavailable(exc)

    async def delete(self, *keys: str) -> None:
        client = await self._get_client()
        if client is None or not keys:
            return
        try:
            await client.delete(*keys)
        except (RedisError, OSError) as exc:
            self._mark_unavailable(exc)

    async def delete_pattern(self, pattern: str) -> None:
        """删除匹配键；小规模业务命名空间下使用 SCAN 保证安全。"""
        client = await self._get_client()
        if client is None:
            return
        try:
            keys = [key async for key in client.scan_iter(match=pattern, count=100)]
            if keys:
                await client.delete(*keys)
        except (RedisError, OSError) as exc:
            self._mark_unavailable(exc)

    async def close(self) -> None:
        if self._client is not None:
            try:
                await self._client.aclose()
            except (RedisError, OSError):
                pass
            self._client = None


cache = CacheManager()


def prescription_list_key(
    page: int,
    page_size: int,
    keyword: Optional[str],
    name: Optional[str],
    type_value: Optional[str],
    category: Optional[str],
    sort_by: str,
    sort_order: str,
) -> str:
    """生成方剂列表缓存键，参数顺序固定。"""
    parts = [
        "prescriptions:list",
        f"page={page}",
        f"size={page_size}",
        f"keyword={keyword or ''}",
        f"name={name or ''}",
        f"type={type_value or ''}",
        f"category={category or ''}",
        f"sort={sort_by}:{sort_order}",
    ]
    return "|".join(parts)


async def invalidate_prescription_cache(prescription_id: Optional[int] = None) -> None:
    """失效方剂详情、列表和分析缓存。"""
    await cache.delete_pattern("prescriptions:*")
    if prescription_id is not None:
        await cache.delete(f"prescription:{prescription_id}:detail")
