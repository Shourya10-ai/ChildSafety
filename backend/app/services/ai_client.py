import httpx
import logging
import asyncio
from typing import Optional, Dict, Any, List
from app.core.config import settings

logger = logging.getLogger(__name__)

class AIClient:
    def __init__(self):
        self.base_url = settings.AI_SERVER_URL or "http://localhost:8001"
        self.timeout = 30.0
    
    async def analyze_text(self, text: str, context_metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        return await self._call_api("/api/v1/analyze/text", {"text": text, "context_metadata": context_metadata})
    
    async def analyze_batch(self, texts: List[str], context_metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        return await self._call_api("/api/v1/analyze/batch", {"texts": texts, "context_metadata": context_metadata})
    
    async def get_rag_guidance(self, query: str) -> Optional[Dict[str, Any]]:
        return await self._call_api("/api/v1/rag/guidance", {"query_text": query})

    async def _call_api(self, endpoint: str, payload: dict) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url.rstrip('/')}{endpoint}"
        retries = 2
        for attempt in range(retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    return response.json()
            except Exception as e:
                if attempt < retries:
                    await asyncio.sleep(2 ** attempt)
                else:
                    logger.error(f"AI API call to {endpoint} failed after {retries} retries: {str(e)}")
        return None

ai_client = AIClient()
