import os
import sys
import ctypes
import logging
import subprocess
from typing import Any, Dict

logger = logging.getLogger(__name__)

class MemoryStatus(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]

def get_system_memory() -> Dict[str, float]:
    """Retrieves system total and available physical RAM in GB."""
    if sys.platform == "win32":
        try:
            stat = MemoryStatus()
            stat.dwLength = ctypes.sizeof(MemoryStatus)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                return {
                    "total_gb": round(stat.ullTotalPhys / (1024**3), 2),
                    "available_gb": round(stat.ullAvailPhys / (1024**3), 2),
                    "memory_load_pct": stat.dwMemoryLoad,
                }
        except Exception as e:
            logger.debug(f"Failed to query GlobalMemoryStatusEx: {e}")
    # Fallback default
    return {"total_gb": 16.0, "available_gb": 6.0, "memory_load_pct": 60}

def get_gpu_info() -> Dict[str, Any]:
    """Detects GPU device and dedicated VRAM."""
    gpu_info = {
        "name": "Unknown / Integrated",
        "has_cuda": False,
        "vram_mb": 0,
        "is_discrete": False,
    }
    if sys.platform == "win32":
        try:
            cmd = "Get-CimInstance Win32_VideoController | Select-Object -First 1 Name, AdapterRAM | ConvertTo-Json"
            out = subprocess.check_output(["powershell", "-NoProfile", "-Command", cmd], text=True, timeout=5)
            import json
            data = json.loads(out)
            gpu_info["name"] = data.get("Name", "Unknown")
            ram_bytes = data.get("AdapterRAM", 0)
            if ram_bytes and isinstance(ram_bytes, (int, float)):
                gpu_info["vram_mb"] = round(ram_bytes / (1024**2))
            if "nvidia" in gpu_info["name"].lower() or "geforce" in gpu_info["name"].lower():
                gpu_info["has_cuda"] = True
                gpu_info["is_discrete"] = True
        except Exception as e:
            logger.debug(f"Failed to query GPU info via CIM: {e}")
    return gpu_info

def detect_runtime_hardware() -> Dict[str, Any]:
    """Inspects host hardware and returns runtime-aware model capability profile."""
    mem = get_system_memory()
    gpu = get_gpu_info()
    cpu_cores = os.cpu_count() or 4

    # Determine capability classification
    total_ram = mem.get("total_gb", 16.0)
    has_cuda = gpu.get("has_cuda", False)
    vram_mb = gpu.get("vram_mb", 0)

    if has_cuda and vram_mb >= 8000:
        profile = "GPU_WORKSTATION"
        can_run_high_tier = True
        reason = "Discrete CUDA GPU with adequate VRAM available."
    elif total_ram >= 64.0:
        profile = "HIGH_MEMORY_SERVER"
        can_run_high_tier = True
        reason = "High memory capacity server able to support large model quantization."
    elif total_ram >= 32.0:
        profile = "WORKSTATION"
        can_run_high_tier = True
        reason = "Multi-core workstation with 32GB+ RAM."
    else:
        profile = "LOW_RESOURCE_CPU"
        can_run_high_tier = False
        reason = (
            f"High-tier local inference ({total_ram:.1f} GB RAM, CPU-only) is disabled on this hardware "
            "because available system memory and the absence of a CUDA-capable GPU make it unsuitable for stable local execution. "
            "Routed to verified local model ai/qwen3:4b-instruct-2507-q4_K_M."
        )

    return {
        "profile": profile,
        "total_ram_gb": total_ram,
        "available_ram_gb": mem.get("available_gb", 0),
        "cpu_cores": cpu_cores,
        "gpu_name": gpu.get("name", "Integrated Graphics"),
        "has_cuda": has_cuda,
        "can_run_high_tier_locally": can_run_high_tier,
        "high_tier_candidate": "ai/qwen3.8-flash-next",
        "recommended_local_model": "ai/qwen3:4b-instruct-2507-q4_K_M",
        "local_model_name": "Qwen3 4B Instruct Q4_K_M",
        "constraint_reason": reason,
    }
