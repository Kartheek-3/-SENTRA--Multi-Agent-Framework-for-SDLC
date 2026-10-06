import json

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import ValidationError

from backend.integrations.n8n.config import get_n8n_config
from backend.integrations.n8n.schemas import N8NEvent, N8NWebhookEvent, N8NWorkflowTriggerRequest
from backend.integrations.n8n.security import constant_time_match
from backend.integrations.n8n.service import N8NIntegrationService


router = APIRouter(prefix="/api/integrations/n8n", tags=["n8n"])


@router.get("/status")
def n8n_status():
    return N8NIntegrationService().status().model_dump()


@router.post("/trigger")
def trigger_n8n_workflow(request: N8NWorkflowTriggerRequest):
    return N8NIntegrationService().trigger_workflow(request).model_dump()


@router.post("/events")
def send_n8n_event(event: N8NEvent):
    return N8NIntegrationService().send_event(event).model_dump()


@router.post("/test")
def test_n8n_event():
    event = N8NEvent(event_type="DELIVERY_COMPLETED", status="TEST", payload={"message": "SEAM n8n integration test"})
    return N8NIntegrationService().send_event(event).model_dump()


@router.post("/webhook")
async def n8n_webhook(
    request: Request,
    x_n8n_api_key: str = Header(default=""),
    x_seam_integration_secret: str = Header(default=""),
):
    config = get_n8n_config()
    service = N8NIntegrationService(config=config)
    supplied_secret = x_seam_integration_secret or x_n8n_api_key
    expected_secret = config.integration_secret or config.api_key
    if not config.authentication_configured or not constant_time_match(supplied_secret, expected_secret):
        service.reject_webhook("unauthenticated")
        raise HTTPException(status_code=401, detail="Invalid n8n webhook authentication")

    body = await request.body()
    try:
        payload = json.loads(body.decode("utf-8") or "{}")
        event = N8NWebhookEvent.model_validate(payload)
    except (json.JSONDecodeError, ValidationError) as exc:
        service.reject_webhook("malformed_payload")
        raise HTTPException(status_code=422, detail=f"Malformed n8n webhook payload: {exc.__class__.__name__}")

    return service.handle_webhook(event)
