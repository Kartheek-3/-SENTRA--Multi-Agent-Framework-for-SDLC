# SEAM Phase 5 — Stable Diffusion XL 1.0 (Docker Model Runner) Validation Report

**Date of Validation:** 2026-10-15  
**Evaluation Lead:** Senior AI Infrastructure Engineer & Docker Model Runner Specialist  
**Target Provider:** Docker Model Runner (`http://127.0.0.1:12434`) — Diffusers Engine  
**Target Model:** `ai/stable-diffusion` (Stable Diffusion XL 1.0)  
**Host Environment:** Windows 11 Home (64-bit), 16 GB RAM, Intel(R) UHD Graphics (Integrated)  
**Final Verdict:** **IMAGE GENERATION NOT AVAILABLE ON CURRENT HOST**

---

## 1. Executive Summary

Phase 5 introduces Stable Diffusion XL 1.0 image generation as an optional, capability-detected visual asset creation provider within SEAM.

### Strict Architectural Principles Enforced:
1. **Separation of Concerns:** Stable Diffusion XL 1.0 produces illustrative visual assets (product illustrations, concept art, presentation visuals, landing-page artwork, abstract system visualization, decorative architecture concepts). It **does not** and **must not** generate or replace canonical, authoritative software engineering diagrams.
2. **Canonical Diagram Engine Preservation:** The existing ten canonical diagram types (`architecture_diagram`, `use_case_diagram`, `class_diagram`, `object_diagram`, `sequence_diagram`, `activity_diagram`, `dfd_level_0`, `dfd_level_1`, `erd_diagram`, `deployment_diagram`) remain governed strictly by Pydantic schemas (`DiagramJSON`), deterministic template extraction, semantic validation (`DiagramValidator`), Dagre layout, and React Flow.
3. **Honest Capability Detection:** Automated probing of the local host platform revealed that Docker Model Runner's documented Diffusers backend (`/engines/diffusers/v1/images/generations`) requires a Linux host with an NVIDIA CUDA-capable GPU. The current host is Windows 11 with Intel UHD Graphics (no CUDA). As mandated, the system accurately reports `NOT_AVAILABLE_ON_CURRENT_HOST` with reason `UNSUPPORTED_DIFFUSERS_PLATFORM_OR_HARDWARE` and prevents destructive or multi-gigabyte downloads.

---

## 2. Provider Architecture

A clean, non-intrusive provider abstraction was introduced without altering the canonical Diagram Engine or the text `ModelRouter`:

```
                           +--------------------------------------+
                           |          Design Studio UI            |
                           +------------------+-------------------+
                                              |
                     +------------------------+------------------------+
                     |                                                 |
         [Engineering Diagrams Mode]                          [Visual Assets Mode]
                     |                                                 |
       +-------------v-------------+                       +-----------v------------+
       | Canonical Diagram Engine  |                       |  Image Generation API  |
       |  - 10 Canonical Types     |                       |  POST /api/images/gen  |
       |  - Pydantic Schema Valid. |                       +-----------+------------+
       |  - React Flow + Dagre     |                                   |
       |  - Mermaid/SVG/PNG Export |                   +---------------v---------------+
       +---------------------------+                   |    ImageGenerationProvider    |
                                                       |         (Interface)           |
                                                       +---------------+---------------+
                                                                       |
                                                       +---------------v---------------+
                                                       |      DockerSDXLProvider       |
                                                       |  - Hardware Detection         |
                                                       |  - Platform Support Check     |
                                                       |  - DMR Endpoint Communication |
                                                       +---------------+---------------+
                                                                       |
                                                       +---------------v---------------+
                                                       |   Docker Model Runner (DMR)   |
                                                       |   http://127.0.0.1:12434      |
                                                       |   /engines/diffusers/v1/...   |
                                                       +-------------------------------+
```

### Components Implemented:
- `backend/image_gen/models.py`: Pydantic request, response, and capability models (`ImageGenerationRequest`, `ImageGenerationResponse`, `CapabilityStatus`, `ImagePurpose`, `ImageArtifactMetadata`).
- `backend/image_gen/provider.py`: `ImageGenerationProvider` abstract class and `DockerSDXLProvider` implementation with `detect_host_hardware()` capability inspection.
- `backend/api/images.py`: FastAPI endpoints (`GET /api/images/capabilities`, `POST /api/images/generate`, `GET /api/images/gallery/{project_id}`).
- `seam-ide/src/api/client.ts`: Typed API client methods (`imageCapabilities()`, `generateImage()`, `listProjectVisualAssets()`).
- `seam-ide/src/components/DesignStudioPage.tsx`: Integrated dual-section Design Studio with separated Engineering Diagrams and Visual Assets studio.

---

## 3. Host Hardware Compatibility & Docker Capability Status

Real, live host inspection was executed on the local environment:

| Attribute | Measured Host Value | DMR / Diffusers Requirement | Status |
| :--- | :--- | :--- | :--- |
| **Operating System** | Windows 11 Home (64-bit) | Linux (Docker engine backend) | **UNSUPPORTED** |
| **GPU Vendor / Model** | Intel(R) UHD Graphics (Integrated) | NVIDIA GPU (Ampere/Ada/Hopper) | **UNSUPPORTED** |
| **CUDA Capability** | None (`has_cuda: false`, no `nvidia-smi`) | CUDA 11.8+ / 12.x | **UNSUPPORTED** |
| **Host System Memory** | 16 GB Physical RAM | $\ge$ 16 GB dedicated VRAM recommended | **MARGINAL** |
| **DMR Listener Status**| Online (`http://127.0.0.1:12434`) | Active daemon on TCP 12434 | **PASS (v1.2.8)** |
| **DMR Diffusers Engine**| Probed: `POST /engines/diffusers/...` | Diffusers image generation endpoint | **ENDPOINT PRESENT** |
| **SDXL Model Installed**| Not in catalog (`ai/qwen3:4b` present) | `ai/stable-diffusion` | **NOT PULLED** |

### Capability Assessment:
Because the host is running Windows with Intel integrated graphics and lacks a CUDA-capable NVIDIA GPU, the system reports:
```json
{
  "status": "NOT_AVAILABLE_ON_CURRENT_HOST",
  "reason": "UNSUPPORTED_DIFFUSERS_PLATFORM_OR_HARDWARE",
  "host_os": "Windows",
  "has_cuda": false,
  "gpu_info": "Intel(R) UHD Graphics",
  "diffusers_supported_on_host": false,
  "explanation": "Docker Model Runner Diffusers backend is not supported on Windows with Intel(R) UHD Graphics. Local Stable Diffusion XL 1.0 requires a Linux host with an NVIDIA CUDA-capable GPU. Visual image generation is disabled on this host to prevent system instability."
}
```

---

## 4. Multi-Gigabyte Download Safeguard

In compliance with prompt Section 6:
- **No Large Downloads Attempted:** The framework did not run `docker pull ai/stable-diffusion` (approx. 6.6 GB download, 13 GB uncompressed).
- **No System Mutation:** Did not alter Docker Desktop WSL2 settings, GPU drivers, or system-level dependencies.
- **Graceful UI Disablement:** The UI identifies the missing hardware, marks the provider as disabled with an explanatory badge, and allows the developer to continue using Engineering Diagrams uninterrupted.

---

## 5. Design Studio UI Integration

The `DesignStudioPage.tsx` interface was updated with a primary mode toggle:
1. **`📐 Engineering Diagrams` (Default):**
   - Retains all 10 canonical diagrams with React Flow canvas, Dagre auto-layout, Visual / Mermaid / JSON tabs, node inspector, and validation.
   - Zero image generation controls clutter the engineering diagram canvas.
2. **`🎨 Visual Assets (Illustrations)`:**
   - **Capability Status Alert:** Clear banner displaying `NOT_AVAILABLE_ON_CURRENT_HOST` with explanation.
   - **Compact Provider Selector:** Displays `Docker SDXL 1.0` (disabled on current host with tooltip explanation).
   - **Prompt Input:** Textarea with 1000-character boundary counter.
   - **Purpose Classification Dropdown:** `Product Illustration`, `Concept Art`, `Presentation Visual`, `Landing Page Artwork`, `Abstract System Visualization`, `Decorative Architecture Concept`, `Supporting Visual Asset`.
   - **Dimensions Selector:** Supported aspect ratios (`1024x1024`, `1152x896`, `896x1152`, `1216x832`, `832x1216`).
   - **Negative Prompt Input:** Optional field for quality tuning.
   - **Generate Action Button:** Disabled with status indicator `Unavailable on Current Host`.
   - **Visual Asset Preview & Gallery:** Displays generated illustrations with metadata viewer (Provider, Model, Dimensions, Purpose, Artifact ID) and quick actions.
   - **Seamless Navigation:** Button to return to Engineering Diagrams instantly.

---

## 6. Artifact Persistence & Event Logging

When executed on a compatible host or in mock verification mode:
- **Registry Binding:** Registered in `ArtifactRegistry` as type `ArtifactType.IMAGE` (or `VISUAL_ASSET`).
- **Disk Isolation:** Stored in `./generated_projects/<project_name>/visual_assets/<purpose>_<timestamp>.png`.
- **Classification Flag:** Metadata explicitly includes `is_authoritative_diagram: false` to ensure visual assets are never mistaken for validated engineering specifications.
- **Event Bus Emissions:** Emits standard events:
  - `IMAGE_GENERATION_STARTED`
  - `IMAGE_GENERATION_COMPLETED`
  - `IMAGE_GENERATION_FAILED`
  - `IMAGE_GENERATION_UNAVAILABLE`
  - `IMAGE_ARTIFACT_PERSISTED`

---

## 7. Security and Validation Controls

- **Prompt Input Boundaries:** String validation enforces $1 \le \text{length} \le 1000$ characters and non-empty content.
- **Dimension Restrictions:** Dimensions strictly restricted to validated SDXL optimal aspect ratios ($\{512, 768, 832, 896, 1024, 1152, 1216\}$).
- **Project Ownership:** Verifies project exists in `projects_db` / SQLite before dispatching requests.
- **Path Confinement:** Image output paths are restricted to `./generated_projects/<project_name>/visual_assets/`.
- **Zero Cloud Leakage:** All inference remains local; no cloud API keys or external services are invoked.

---

## 8. Test Execution Summary

A dedicated, comprehensive test suite was implemented in `SEAM/tests/test_phase5_docker_sdxl.py`:

| Test Name | Focus | Result |
| :--- | :--- | :--- |
| `test_detect_host_hardware` | Detects Windows 11 and Intel UHD Graphics accurately | **PASS** |
| `test_docker_sdxl_provider_capability_detection_current_host` | Live check asserts `NOT_AVAILABLE_ON_CURRENT_HOST` | **PASS** |
| `test_docker_sdxl_provider_rejection_on_non_cuda_linux` | Asserts non-CUDA Linux is rejected | **PASS** |
| `test_docker_sdxl_provider_offline_handling` | Asserts offline DMR returns `NOT_CONFIGURED` | **PASS** |
| `test_docker_sdxl_provider_model_missing_handling` | Asserts missing SDXL model returns `UNSUPPORTED_MODEL` | **PASS** |
| `test_image_generation_request_validation` | Validates prompt length, dimensions, empty strings | **PASS** |
| `test_generation_refusal_on_unsupported_host` | Asserts `generate_image` returns structured denial | **PASS** |
| `test_successful_mocked_image_generation_and_artifact_persistence` | Tests mock generation, disk write, and `ArtifactRegistry` | **PASS** |
| `test_malformed_dmr_response_handling` | Tests empty or corrupt DMR diffusers response | **PASS** |
| `test_api_images_capabilities_endpoint` | Tests FastAPI `GET /api/images/capabilities` | **PASS** |
| `test_api_images_generate_unknown_project` | Tests FastAPI `POST /api/images/generate` 404 handling | **PASS** |
| `test_api_images_generate_on_current_host` | Tests FastAPI `POST /api/images/generate` capability denial | **PASS** |
| `test_separation_between_visual_assets_and_engineering_diagrams` | Confirms all 10 canonical diagrams remain untouched | **PASS** |

**Phase 5 Test Suite Result:** **13 passed in 27.27s** (100% PASS).

---

## 9. Full System Regression

Following the Phase 5 implementation, all regression suites were executed:

1. **Backend Pytest Suite:**
   - Command: `python -m pytest -q`
   - Total Tests: **300 passed** (increased from 287 baseline + 13 Phase 5 tests)
   - Failures: **0**
   - Warnings: **0**
   - Duration: 1192.14s (19m 52s)
2. **Frontend Static Typecheck:**
   - Command: `npx.cmd tsc --noEmit`
   - Result: **0 errors**
3. **Frontend Production Build:**
   - Command: `npm.cmd run build` (`tsc -b && vite build`)
   - Result: **0 errors** (627 modules transformed in 8.59s)
4. **Frontend Vitest Suite:**
   - Command: `npx.cmd vitest run`
   - Result: **11 passed (100%)**
5. **Playwright E2E Browser Suite:**
   - Command: `python tests/test_playwright_ui.py`
   - Result: **15 screens verified, 0 errors, 100% PASS**

---

## 10. Live Inference Disclosure

> [!IMPORTANT]
> **Did real local image inference actually execute on this host?**  
> **NO.** Real Stable Diffusion XL 1.0 image inference did not execute because the current host environment (Windows 11 with Intel UHD Graphics and no CUDA-capable NVIDIA GPU) is fundamentally unsupported by Docker Model Runner's Diffusers engine. Capability detection, endpoint routing, provider abstraction, input validation, UI states, artifact persistence, and event logging were fully verified using real host probes and mocked engine responses. No simulated success was claimed.

---

## 11. Steps Required to Enable Generation on a Compatible Host

To execute live local SDXL image generation on a compatible machine:
1. **Hardware Requirements:**
   - Linux host (Ubuntu 22.04 LTS or 24.04 LTS recommended).
   - NVIDIA GPU with $\ge$ 12 GB VRAM (RTX 3060 12GB, RTX 4070/4080/4090, or A4000/A5000/A6000).
   - NVIDIA Container Toolkit and NVIDIA Drivers 535+.
2. **Docker Model Runner Setup:**
   - Start Docker Desktop or Docker Engine with Docker Model Runner enabled (`port 12434`).
   - Pull the official Docker Hub SDXL package:
     ```bash
     docker model pull ai/stable-diffusion
     ```
3. **SEAM Environment Configuration:**
   - In SEAM backend `.env`:
     ```bash
     DMR_BASE_URL=http://127.0.0.1:12434
     SEAM_SDXL_MODEL=ai/stable-diffusion
     ```
   - Restart SEAM backend. Capability detection will transition status from `NOT_AVAILABLE_ON_CURRENT_HOST` to `READY`.

---

## 12. Final Certification Decision

| Verification Dimension | Status | Notes |
| :--- | :--- | :--- |
| **Provider Abstraction** | `PASS` | Clean `ImageGenerationProvider` & `DockerSDXLProvider` |
| **Canonical Diagram Preservation** | `PASS` | All 10 canonical diagrams completely untouched |
| **Authoritative Separation** | `PASS` | Visual assets classified strictly as illustrative artwork |
| **Hardware Detection** | `PASS` | Accurately identifies Windows 11 + Intel UHD (no CUDA) |
| **Download Prevention** | `PASS` | Refuses multi-gigabyte download on incompatible host |
| **FastAPI Endpoints** | `PASS` | Capabilities, generate, and gallery endpoints verified |
| **Design Studio Integration** | `PASS` | Dual-mode tab toggle, capability banner, provider selector |
| **Artifact Persistence** | `PASS` | `ArtifactRegistry` registration with `IMAGE` type |
| **Phase 5 Pytest Suite** | `PASS` | 13/13 tests passed |
| **Full Pytest Regression** | `PASS` | 300/300 tests passed, 0 warnings |
| **Frontend TypeScript Build** | `PASS` | `tsc --noEmit` & `npm run build` 0 errors |
| **Frontend Vitest Suite** | `PASS` | 11/11 tests passed |
| **Playwright Browser Audit** | `PASS` | 15 views, 0 errors |

### **FINAL VERDICT:**
# **IMAGE GENERATION NOT AVAILABLE ON CURRENT HOST**
*(Framework integration complete, safe, and fully tested; disabled honestly due to host hardware/platform constraints)*
