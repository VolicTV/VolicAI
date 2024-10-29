from typing import Callable, Any, Optional
import asyncio
import time
from datetime import datetime, timedelta
from functools import wraps
import logging
from .valorant_exceptions import RateLimitError
from utils.logger import command_logger

class RateLimiter:
    """Handles rate limiting for Valorant API requests"""

    def __init__(self, requests_per_second: int = 50, requests_per_minute: int = 1000):
        self.requests_per_second = requests_per_second
        self.requests_per_minute = requests_per_minute
        self.requests = []
        self.last_request = 0

    async def wait_if_needed(self):
        """Wait if we're approaching rate limits"""
        current_time = time.time()
        
        # Clean up old requests
        self.requests = [req for req in self.requests 
                        if current_time - req < 60]

        # Check minute limit
        if len(self.requests) >= self.requests_per_minute:
            wait_time = 60 - (current_time - self.requests[0])
            if wait_time > 0:
                command_logger.warning(f"Rate limit approaching, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)

        # Check per-second limit
        if current_time - self.last_request < (1.0 / self.requests_per_second):
            wait_time = (1.0 / self.requests_per_second) - (current_time - self.last_request)
            await asyncio.sleep(wait_time)

        self.requests.append(current_time)
        self.last_request = current_time

class RetryHandler:
    """Handles retrying failed API requests"""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    async def retry_with_backoff(self, func: Callable, *args, **kwargs) -> Any:
        """
        Retry a function with exponential backoff
        
        Args:
            func: Function to retry
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Any: Function result
            
        Raises:
            RateLimitError: If rate limit is hit and retries exhausted
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except RateLimitError as e:
                last_exception = e
                delay = self.base_delay * (2 ** attempt)
                command_logger.warning(
                    f"Rate limit hit, attempt {attempt + 1}/{self.max_retries}, "
                    f"waiting {delay:.2f}s"
                )
                await asyncio.sleep(delay)
            except Exception as e:
                command_logger.error(f"Unexpected error during retry: {str(e)}")
                raise

        raise last_exception or Exception("Max retries exceeded")

def rate_limited(requests_per_second: int = 50, requests_per_minute: int = 1000):
    """
    Decorator for rate-limiting API calls
    
    Args:
        requests_per_second: Maximum requests per second
        requests_per_minute: Maximum requests per minute
    """
    limiter = RateLimiter(requests_per_second, requests_per_minute)

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            await limiter.wait_if_needed()
            return await func(*args, **kwargs)
        return wrapper
    return decorator

class APIThrottler:
    """Manages API request throttling and caching"""

    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.retry_handler = RetryHandler()
        self.last_requests = {}
        self.cooldowns = {}

    async def execute(self, 
                     func: Callable, 
                     cache_key: Optional[str] = None,
                     cooldown: Optional[int] = None,
                     *args, **kwargs) -> Any:
        """
        Execute an API request with throttling and caching
        
        Args:
            func: Function to execute
            cache_key: Optional cache key
            cooldown: Optional cooldown in seconds
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Any: Function result
        """
        # Check cooldown
        if cooldown and cache_key:
            last_request = self.cooldowns.get(cache_key)
            if last_request:
                time_passed = (datetime.utcnow() - last_request).total_seconds()
                if time_passed < cooldown:
                    remaining = cooldown - time_passed
                    raise RateLimitError(
                        f"Request on cooldown. Try again in {remaining:.1f}s"
                    )

        # Execute request
        try:
            await self.rate_limiter.wait_if_needed()
            result = await self.retry_handler.retry_with_backoff(func, *args, **kwargs)
            
            # Update cooldown
            if cooldown and cache_key:
                self.cooldowns[cache_key] = datetime.utcnow()
                
            return result
            
        except Exception as e:
            command_logger.error(f"Error executing API request: {str(e)}")
            raise 