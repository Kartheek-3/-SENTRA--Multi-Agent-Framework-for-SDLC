# SEAM Qwen Runtime Diagnostic

Date: 2026-09-20

## Environment

| Component | Result |
|---|---|
| Python | 3.12.10 |
| Ollama | 0.34.2 |
| Docker | 29.7.2 |
| Ollama server `/api/tags` | HTTP 200 in 0.026s |

## Model

Primary SEAM model remains:

```text
qwen3-coder-next:latest
```

`ollama list` shows:

```text
qwen3-coder-next:latest    ca06e9e4087c    51 GB
qwen2.5-coder:7b           dae161e27b0e    4.7 GB
```

`ollama show qwen3-coder-next:latest`:

```text
architecture        qwen3next
parameters          79.7B
context length      262144
quantization        Q4_K_M
capabilities        completion, tools
```

## Direct API Tests

| Test | Result | Duration |
|---|---|---:|
| `/api/tags` | SUCCESS, HTTP 200, qwen3 listed | 0.026s |
| `/api/generate` qwen3, prompt `Say hello.` | TIMEOUT, HTTP client read timeout | 60.16s |
| `/api/chat` qwen3, prompt `Hello.` | TIMEOUT, HTTP client read timeout | 60.28s |
| `/api/generate` qwen2.5-coder:7b, prompt `Say hello.` | SUCCESS, HTTP 200, response: `Hello! How can I assist you today` | 12.33s |
| Previous qwen3 direct generation attempt | TIMEOUT | ~62.76s |

## Resource Evidence

| Resource | Evidence |
|---|---|
| System RAM | 15.64 GB total |
| Free RAM | observed around 9.87 GB, 6.99 GB, then 11.07 GB |
| CPU | 16 logical processors |
| GPU | Intel(R) UHD Graphics |
| GPU VRAM / NVIDIA | `nvidia-smi` not available; no NVIDIA GPU evidence |
| Disk | C: about 224 GB free |
| Ollama loaded runners | `ollama ps` showed qwen2.5-coder:7b loaded after the successful 7B test; qwen3 did not remain loaded |

## Ollama Logs

Relevant Ollama log path:

```text
C:\Users\KARTHIK\AppData\Local\Ollama\server-1.log
```

Relevant findings:

```text
print_info: arch = qwen3next
load_tensors: CPU model buffer size = 20817.06 MiB
load_tensors: CPU_REPACK model buffer size = 28521.28 MiB
waiting for llama-server to become available status="llm server loading model"
waiting for llama-server to become available status="llm server not responding"
```

The log repeatedly alternates between model loading and server-not-responding states during qwen3 startup.

## Root Cause

Evidence-supported root cause:

```text
qwen3-coder-next:latest is too large for the currently available local runtime resources to load/respond within the bounded validation window.
```

Evidence:

- qwen3 is a 79.7B parameter, 51 GB local model.
- Ollama logs show qwen3 requires about 20.8 GiB CPU model buffer plus 28.5 GiB CPU_REPACK buffer.
- The machine reports 15.64 GB system RAM.
- No NVIDIA GPU/VRAM is visible.
- qwen3 `/api/generate` and `/api/chat` both time out after 60 seconds.
- qwen2.5-coder:7b succeeds through the same Ollama server in 12.33 seconds.

## SEAM Impact

| Layer | Status |
|---|---|
| Ollama server | HEALTHY |
| Ollama model registry | HEALTHY |
| qwen2.5 generation | HEALTHY |
| qwen3-coder-next generation | BLOCKED / TIMEOUT |
| ChatOllama | Not the primary root cause; direct Ollama HTTP also times out |
| ModelRouter | Health works; generation blocked because qwen3 runtime does not return |
| SEAM E2E | BLOCKED until qwen3 generation completes reliably or runtime resources change |

## Next Action

Do not switch SEAM's primary model silently.

Recommended next step:

- Run qwen3-coder-next on hardware with enough RAM/VRAM for a 79.7B Q4 model, or configure Ollama/runtime resources appropriately.
- Re-test direct `/api/generate` before running SEAM E2E again.
