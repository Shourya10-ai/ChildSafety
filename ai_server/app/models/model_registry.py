from __future__ import annotations
import logging
import threading
from typing import Any, Callable, Dict, Optional
import torch
from app.core.config import settings

logger = logging.getLogger(__name__)

class ModelRegistry:
    _instance: Optional[ModelRegistry] = None
    _lock = threading.Lock()

    def __new__(cls) -> ModelRegistry:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ModelRegistry, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if not getattr(self, '_initialized', False):
            with self._lock:
                if not getattr(self, '_initialized', False):
                    self._models: Dict[str, Any] = {}
                    self._loaders: Dict[str, Callable[[], Any]] = {}
                    self._model_locks: Dict[str, threading.Lock] = {}
                    self._device = self._determine_device()
                    self._initialized = True
                    logger.info(f"ModelRegistry initialized with device: {self._device}")

    def _determine_device(self) -> torch.device:
        if settings.DEVICE.lower() == 'cuda' and torch.cuda.is_available():
            return torch.device('cuda')
        elif settings.DEVICE.lower() == 'cuda' and not torch.cuda.is_available():
            logger.warning("CUDA requested but not available. Falling back to CPU.")
            return torch.device('cpu')
        return torch.device('cpu')

    def get_device(self) -> torch.device:
        return self._device

    def register(self, name: str, loader_fn: Callable[[], Any]) -> None:
        with self._lock:
            self._loaders[name] = loader_fn
            if name not in self._model_locks:
                self._model_locks[name] = threading.Lock()
            logger.info(f"Registered model loader for '{name}'")

    def get(self, name: str) -> Any:
        if name not in self._loaders and name not in self._models:
            raise ValueError(f"Model '{name}' is not registered.")
        
        if name not in self._models:
            with self._model_locks.get(name, self._lock):
                if name not in self._models:
                    logger.info(f"Loading model '{name}'...")
                    try:
                        self._models[name] = self._loaders[name]()
                        logger.info(f"Successfully loaded model '{name}'")
                    except Exception as e:
                        logger.error(f"Failed to load model '{name}': {e}")
                        raise
        return self._models[name]

    def load_all(self) -> None:
        logger.info("Pre-loading all registered models...")
        for name in list(self._loaders.keys()):
            self.get(name)
        logger.info("Finished pre-loading all models.")

    def unload(self, name: str) -> None:
        with self._model_locks.get(name, self._lock):
            if name in self._models:
                del self._models[name]
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                logger.info(f"Unloaded model '{name}'")
            else:
                logger.info(f"Model '{name}' is not loaded.")

    def list_models(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            status = {}
            for name in self._loaders.keys():
                status[name] = {
                    "loaded": name in self._models,
                    "device": str(self._device)
                }
            return status
