import asyncio
import aiohttp
import random
import logging
from typing import List, Dict, Optional
import httpx
from dataclasses import dataclass, field
from datetime import datetime, timedelta

@dataclass
class ProxyMetrics:
    success_rate: float = 0.0
    total_requests: int = 0
    successful_requests: int = 0
    last_used: Optional[datetime] = None
    consecutive_failures: int = 0

@dataclass
class ProxyConfig:
    host: str
    port: int
    protocol: str = 'http'
    username: Optional[str] = None
    password: Optional[str] = None
    metrics: ProxyMetrics = field(default_factory=ProxyMetrics)

class ProxyManager:
    def __init__(
        self, 
        proxy_list: Optional[List[str]] = None, 
        max_failures: int = 3,
        rotation_interval: int = 300  # 5 minutes
    ):
        self.proxies: List[ProxyConfig] = []
        self.max_failures = max_failures
        self.rotation_interval = rotation_interval
        self.logger = logging.getLogger(__name__)
        
        # Load proxies
        if proxy_list:
            self.load_proxies(proxy_list)

    def load_proxies(self, proxy_list: List[str]):
        """
        Load proxies from list of strings
        Format: 
        - 'http://host:port'
        - 'http://username:password@host:port'
        """
        for proxy_str in proxy_list:
            try:
                parsed_proxy = self._parse_proxy_string(proxy_str)
                self.proxies.append(parsed_proxy)
            except ValueError as e:
                self.logger.error(f"Invalid proxy format: {proxy_str}")

    def _parse_proxy_string(self, proxy_str: str) -> ProxyConfig:
        """Parse proxy string into ProxyConfig"""
        try:
            # Split protocol
            protocol, rest = proxy_str.split('://', 1)
            
            # Check for authentication
            if '@' in rest:
                auth, connection = rest.split('@')
                username, password = auth.split(':')
                host, port = connection.split(':')
            else:
                username = password = None
                host, port = rest.split(':')

            return ProxyConfig(
                host=host,
                port=int(port),
                protocol=protocol,
                username=username,
                password=password
            )
        except Exception:
            raise ValueError(f"Invalid proxy format: {proxy_str}")

    def get_proxy_url(self, proxy: ProxyConfig) -> str:
        """Generate full proxy URL"""
        if proxy.username and proxy.password:
            return f"{proxy.protocol}://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}"
        return f"{proxy.protocol}://{proxy.host}:{proxy.port}"

    async def validate_proxy(self, proxy: ProxyConfig, timeout: float = 5.0) -> bool:
        """
        Validate proxy by testing connection
        Test sites: Google, GitHub, etc.
        """
        test_urls = [
            'https://www.google.com',
            'https://github.com',
            'https://www.cloudflare.com'
        ]
        
        proxy_url = self.get_proxy_url(proxy)
        proxies = {
            'http://': proxy_url,
            'https://': proxy_url
        }

        try:
            async with httpx.AsyncClient(
                proxies=proxies, 
                timeout=timeout
            ) as client:
                for url in test_urls:
                    response = await client.get(url)
                    if response.status_code == 200:
                        return True
        except Exception as e:
            self.logger.debug(f"Proxy validation failed: {proxy_url} - {e}")
        
        return False

    def select_best_proxy(self) -> Optional[ProxyConfig]:
        """
        Select best proxy based on:
        1. Success rate
        2. Least consecutive failures
        3. Not recently used
        """
        if not self.proxies:
            return None

        valid_proxies = [
            proxy for proxy in self.proxies 
            if (proxy.metrics.consecutive_failures < self.max_failures and
                (proxy.metrics.last_used is None or 
                 datetime.now() - proxy.metrics.last_used > timedelta(seconds=self.rotation_interval)))
        ]

        if not valid_proxies:
            # Reset failures if all proxies are blocked
            for proxy in self.proxies:
                proxy.metrics.consecutive_failures = 0
            valid_proxies = self.proxies

        return max(
            valid_proxies, 
            key=lambda p: (p.metrics.success_rate, -p.metrics.consecutive_failures)
        )

    def update_proxy_metrics(
        self, 
        proxy: ProxyConfig, 
        success: bool
    ):
        """Update proxy performance metrics"""
        proxy.metrics.total_requests += 1
        proxy.metrics.last_used = datetime.now()

        if success:
            proxy.metrics.successful_requests += 1
            proxy.metrics.consecutive_failures = 0
        else:
            proxy.metrics.consecutive_failures += 1

        # Recalculate success rate
        proxy.metrics.success_rate = (
            proxy.metrics.successful_requests / 
            proxy.metrics.total_requests
        ) if proxy.metrics.total_requests > 0 else 0.0

    async def download_with_proxy(
        self, 
        url: str, 
        method: str = 'GET', 
        **kwargs
    ):
        """
        Download content using best available proxy
        Automatically handles proxy rotation and validation
        """
        proxy = self.select_best_proxy()
        if not proxy:
            # Fallback to direct connection
            async with httpx.AsyncClient() as client:
                response = await client.request(method, url, **kwargs)
                return response

        proxy_url = self.get_proxy_url(proxy)
        proxies = {
            'http://': proxy_url,
            'https://': proxy_url
        }

        try:
            async with httpx.AsyncClient(
                proxies=proxies, 
                timeout=kwargs.pop('timeout', 10.0)
            ) as client:
                response = await client.request(method, url, **kwargs)
                
                # Mark proxy as successful
                self.update_proxy_metrics(proxy, success=True)
                return response

        except Exception as e:
            self.logger.warning(f"Proxy download failed: {e}")
            
            # Mark proxy as failed
            self.update_proxy_metrics(proxy, success=False)
            
            # Retry without proxy
            return await self.download_with_proxy(url, method, **kwargs)

    def get_proxy_stats(self) -> List[Dict]:
        """Get detailed proxy performance statistics"""
        return [
            {
                'host': proxy.host,
                'port': proxy.port,
                'protocol': proxy.protocol,
                'success_rate': proxy.metrics.success_rate,
                'total_requests': proxy.metrics.total_requests,
                'consecutive_failures': proxy.metrics.consecutive_failures
            }
            for proxy in self.proxies
        ]

# Example Usage
async def main():
    proxy_manager = ProxyManager([
        'http://proxy1.example.com:8080',
        'https://username:password@proxy2.example.com:443'
    ])

    # Download with automatic proxy management
    response = await proxy_manager.download_with_proxy('https://example.com')
    
    # Get proxy performance statistics
    stats = proxy_manager.get_proxy_stats()
    print(stats)

if __name__ == '__main__':
    asyncio.run(main())