from __future__ import annotations
import torch
from fastapi import APIRouter
from app.models.model_registry import ModelRegistry

router = APIRouter()

@router.get("")
@router.get("/")
async def get_health():
    registry = ModelRegistry()
    device_str = str(registry.get_device())
    models_info = registry.list_models()
    loaded_models = [m for m, info in models_info.items() if info["loaded"]]
    return {
        "status": "healthy",
        "models_loaded": loaded_models,
        "device": device_str
    }

@router.get("/models")
async def get_models_health():
    registry = ModelRegistry()
    return {
        "registry_status": registry.list_models()
    }

@router.get("/gpu")
async def get_gpu_health():
    if not torch.cuda.is_available():
        return {
            "cuda_available": False,
            "device_count": 0,
            "current_device": None,
            "memory_allocated_mb": 0,
            "memory_reserved_mb": 0
        }
    
    current_device = torch.cuda.current_device()
    return {
        "cuda_available": True,
        "device_count": torch.cuda.device_count(),
        "current_device": current_device,
        "device_name": torch.cuda.get_device_name(current_device),
        "memory_allocated_mb": round(torch.cuda.memory_allocated(current_device) / (1024 ** 2), 2),
        "memory_reserved_mb": round(torch.cuda.memory_reserved(current_device) / (1024 ** 2), 2)
    }
