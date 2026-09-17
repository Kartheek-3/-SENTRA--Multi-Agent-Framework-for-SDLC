import os
from concurrent.futures import ThreadPoolExecutor
from threading import BoundedSemaphore


MAX_LLM_CONCURRENCY = int(os.getenv("SEAM_MAX_LLM_CONCURRENCY", "2"))
MAX_DIAGRAM_CONCURRENCY = int(os.getenv("SEAM_MAX_DIAGRAM_CONCURRENCY", "2"))
MAX_WORKFLOW_CONCURRENCY = int(os.getenv("SEAM_MAX_WORKFLOW_CONCURRENCY", "1"))

llm_semaphore = BoundedSemaphore(MAX_LLM_CONCURRENCY)
diagram_executor = ThreadPoolExecutor(max_workers=MAX_DIAGRAM_CONCURRENCY, thread_name_prefix="seam-diagram")
workflow_executor = ThreadPoolExecutor(max_workers=MAX_WORKFLOW_CONCURRENCY, thread_name_prefix="seam-workflow")
