"""
재시도 로직 유틸리티

API 호출 실패 시 자동 재시도
"""

import asyncio
import functools
from typing import Callable, Any

from .logger import get_logger


logger = get_logger(__name__)


def with_retry(max_attempts: int = 3, delay: float = 1.0, exponential_backoff: bool = True):
    """비동기 함수 재시도 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        logger.error(f"{func.__name__} 최대 재시도 수 초과: {e}")
                        raise
                    
                    wait_time = delay * (2 ** attempt if exponential_backoff else 1)
                    logger.warning(f"{func.__name__} 실패 (attempt {attempt + 1}/{max_attempts}): {e}. {wait_time}초 후 재시도")
                    
                    await asyncio.sleep(wait_time)
            
            raise last_exception
        
        return wrapper
    return decorator


def sync_retry(max_attempts: int = 3, delay: float = 1.0):
    """동기 함수 재시도 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            import time
            
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        logger.error(f"{func.__name__} 최대 재시도 수 초과: {e}")
                        raise
                    
                    logger.warning(f"{func.__name__} 실패 (attempt {attempt + 1}/{max_attempts}): {e}. {delay}초 후 재시도")
                    time.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator