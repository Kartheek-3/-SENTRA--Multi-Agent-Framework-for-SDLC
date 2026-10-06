import json
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

from backend.models.contracts import (
    APIContract,
    APIParameter,
    APIRequestSchema,
    APIResponseSchema,
    ContractIssue,
    ContractMapping,
    DatabaseEntityContract,
    FrontendAPIUsage,
    FullStackContractProfile,
)


def build_full_stack_contract_profile(state) -> FullStackContractProfile:
    api_contracts = [_api_contract(endpoint) for endpoint in _api_endpoints(state)]
    database_entities = [_database_contract(entity) for entity in _database_entities(state)]
    frontend_usage = _frontend_usages(state)
    mappings = _contract_mappings(state, frontend_usage, api_contracts, database_entities)
    profile = FullStackContractProfile(
        api_contracts=api_contracts,
        frontend_api_usage=frontend_usage,
        database_entities=database_entities,
        mappings=mappings,
        traceability=[_traceability_item(mapping) for mapping in mappings],
        source_summary={
            "frontend_architecture_plan": bool(getattr(state, "frontend_architecture_plan", None)),
            "api_endpoints": len(api_contracts),
            "database_entities": len(database_entities),
            "frontend_api_usage": len(frontend_usage),
        },
    )
    profile.issues = validate_full_stack_contract(profile)
    profile.status = "PASS" if not any(issue.severity in ("ERROR", "BLOCKER") for issue in profile.issues) else "FAIL"
    return profile


def validate_full_stack_contract(profile: FullStackContractProfile) -> List[ContractIssue]:
    issues: List[ContractIssue] = []
    api_by_endpoint = {_api_key(api.method, api.endpoint): api for api in profile.api_contracts}
    endpoint_paths = {api.endpoint: api for api in profile.api_contracts}

    for usage in profile.frontend_api_usage:
        key = _api_key(usage.method, usage.endpoint)
        api = api_by_endpoint.get(key)
        if not api:
            same_path = endpoint_paths.get(usage.endpoint)
            if same_path:
                issues.append(_issue(
                    "HTTP_METHOD_MISMATCH",
                    "ERROR",
                    usage.service or usage.frontend_page,
                    same_path.backend_implementation or "SystemDesign",
                    usage.frontend_file,
                    usage.endpoint,
                    "",
                    same_path.method,
                    usage.method,
                    f"Frontend calls {usage.method} {usage.endpoint}, but backend contract exposes {same_path.method} {same_path.endpoint}.",
                    "Align the frontend HTTP method or update the backend contract intentionally.",
                ))
            else:
                issues.append(_issue(
                    "MISSING_BACKEND_ENDPOINT",
                    "ERROR",
                    usage.service or usage.frontend_page,
                    "SystemDesign.api_endpoints",
                    usage.frontend_file,
                    usage.endpoint,
                    "",
                    "backend endpoint",
                    "not found",
                    f"Frontend references {usage.method} {usage.endpoint}, but no matching backend API contract exists.",
                    "Add the backend endpoint to SystemDesign/API implementation or update the frontend service endpoint.",
                ))
            continue
        if usage.request_schema and api.request_body and api.request_body.name and usage.request_schema != api.request_body.name:
            issues.append(_issue(
                "REQUEST_SCHEMA_MISMATCH",
                "WARNING",
                usage.request_schema,
                api.request_body.name,
                usage.frontend_file,
                usage.endpoint,
                "",
                api.request_body.name,
                usage.request_schema,
                "Frontend request schema name differs from backend request schema.",
                "Use the backend request schema name in frontend types or update the API contract.",
            ))
        if usage.response_schema and api.response_body and api.response_body.name and usage.response_schema != api.response_body.name:
            issues.append(_issue(
                "RESPONSE_SCHEMA_MISMATCH",
                "WARNING",
                usage.response_schema,
                api.response_body.name,
                usage.frontend_file,
                usage.endpoint,
                "",
                api.response_body.name,
                usage.response_schema,
                "Frontend response schema name differs from backend response schema.",
                "Align frontend response type with backend contract or update the API response model.",
            ))

    frontend_keys = {_api_key(usage.method, usage.endpoint) for usage in profile.frontend_api_usage}
    for api in profile.api_contracts:
        if frontend_keys and _api_key(api.method, api.endpoint) not in frontend_keys:
            issues.append(_issue(
                "MISSING_FRONTEND_API_USAGE",
                "INFO",
                "SystemDesign.api_endpoints",
                "FrontendArchitecturePlan",
                "",
                api.endpoint,
                "",
                f"{api.method} {api.endpoint}",
                "no frontend caller mapped",
                "Backend API contract has no mapped frontend caller in the current frontend architecture plan.",
                "Add frontend service usage if the endpoint is user-facing, otherwise keep it as backend-only.",
            ))

    for mapping in profile.mappings:
        if mapping.api and not mapping.database_entity and _endpoint_suggests_persistence(mapping.api.endpoint):
            issues.append(_issue(
                "MISSING_DATABASE_MAPPING",
                "WARNING",
                mapping.api.endpoint,
                "SystemDesign.database_schema",
                mapping.frontend.frontend_file if mapping.frontend else "",
                mapping.api.endpoint,
                "",
                "database entity",
                "not mapped",
                "Persistent-looking API endpoint has no mapped database entity.",
                "Map the API contract to the database entity/table or mark it as non-persistent in the design.",
            ))

    return issues


def _api_endpoints(state) -> Iterable[Any]:
    design = getattr(state, "system_design", None) or getattr(getattr(state, "project_plan", None), "system_design", None)
    return getattr(design, "api_endpoints", []) or []


def _database_entities(state) -> Iterable[Any]:
    design = getattr(state, "system_design", None) or getattr(getattr(state, "project_plan", None), "system_design", None)
    return getattr(design, "database_schema", []) or []


def _api_contract(endpoint) -> APIContract:
    request_fields = _schema_fields(getattr(endpoint, "request_schema", "{}"))
    response_fields = _schema_fields(getattr(endpoint, "response_schema", "{}"))
    path_params = [
        APIParameter(name=name, location="path", required=True)
        for name in re.findall(r"{([^}/]+)}", getattr(endpoint, "path", ""))
    ]
    return APIContract(
        method=(getattr(endpoint, "method", "") or "GET").upper(),
        endpoint=getattr(endpoint, "path", ""),
        purpose=getattr(endpoint, "purpose", ""),
        path_parameters=path_params,
        request_body=APIRequestSchema(name=_schema_name(getattr(endpoint, "request_schema", "")), fields=request_fields, raw_schema=getattr(endpoint, "request_schema", "{}")),
        response_body=APIResponseSchema(name=_schema_name(getattr(endpoint, "response_schema", "")), fields=response_fields, raw_schema=getattr(endpoint, "response_schema", "{}"), status_codes=_default_status_codes(getattr(endpoint, "method", ""))),
        authentication_required=bool(getattr(endpoint, "authentication_required", False)),
        status_codes=_default_status_codes(getattr(endpoint, "method", "")),
        backend_implementation="SystemDesign.api_endpoints",
    )


def _database_contract(entity) -> DatabaseEntityContract:
    name = getattr(entity, "name", "")
    return DatabaseEntityContract(
        name=name,
        table=_table_name(name),
        fields=list(getattr(entity, "fields", []) or []),
        relationships=list(getattr(entity, "relationships", []) or []),
    )


def _frontend_usages(state) -> List[FrontendAPIUsage]:
    plan = getattr(state, "frontend_architecture_plan", None)
    if not plan:
        return []
    usages: List[FrontendAPIUsage] = []
    file_by_service = {}
    for service in getattr(plan, "services", []) or []:
        files = getattr(service, "files", []) or []
        file_by_service[service.name] = files[0] if files else f"src/services/{service.name[0].lower() + service.name[1:]}.ts"
    for integration in getattr(plan, "api_integration", []) or []:
        service = getattr(integration, "service", "")
        page = getattr(integration, "page", "")
        for endpoint_label in getattr(integration, "endpoints", []) or []:
            method, endpoint = _split_endpoint_label(endpoint_label)
            usages.append(FrontendAPIUsage(
                frontend_page=page,
                frontend_component=_component_for_page(plan, page),
                frontend_file=file_by_service.get(service, ""),
                service=service,
                function=_function_name(method, endpoint),
                method=method,
                endpoint=endpoint,
            ))
    return usages


def _contract_mappings(state, usages, api_contracts, database_entities) -> List[ContractMapping]:
    api_by_key = {_api_key(api.method, api.endpoint): api for api in api_contracts}
    mappings: List[ContractMapping] = []
    frontend_plan = getattr(state, "frontend_architecture_plan", None)
    trace_items = getattr(frontend_plan, "traceability", []) if frontend_plan else []
    if usages:
        for usage in usages:
            api = api_by_key.get(_api_key(usage.method, usage.endpoint))
            db = _match_database_entity(api, database_entities) if api else None
            trace = _matching_trace(trace_items, usage)
            mappings.append(ContractMapping(
                requirement_id=getattr(trace, "requirement_id", ""),
                requirement=getattr(trace, "requirement", ""),
                frontend=usage,
                api=api,
                backend_model=_schema_model_name(api.response_body if api else None),
                database_entity=db,
                field_mappings=_field_mappings(api, db),
                status="MATCH" if api else "MISMATCH",
            ))
    else:
        for api in api_contracts:
            db = _match_database_entity(api, database_entities)
            mappings.append(ContractMapping(
                api=api,
                backend_model=_schema_model_name(api.response_body),
                database_entity=db,
                field_mappings=_field_mappings(api, db),
                status="BACKEND_ONLY",
            ))
    return mappings


def _traceability_item(mapping: ContractMapping) -> Dict[str, Any]:
    frontend = mapping.frontend
    api = mapping.api
    db = mapping.database_entity
    return {
        "requirement_id": mapping.requirement_id,
        "requirement": mapping.requirement,
        "frontend_page": frontend.frontend_page if frontend else "",
        "frontend_component": frontend.frontend_component if frontend else "",
        "frontend_file": frontend.frontend_file if frontend else "",
        "api": f"{api.method} {api.endpoint}" if api else "",
        "backend_model": mapping.backend_model,
        "database_entity": db.name if db else "",
        "status": mapping.status,
    }


def _schema_fields(raw_schema: str) -> Dict[str, Any]:
    if not raw_schema or raw_schema == "{}":
        return {}
    try:
        parsed = json.loads(raw_schema)
    except Exception:
        return {}
    if isinstance(parsed, dict):
        if isinstance(parsed.get("properties"), dict):
            return parsed["properties"]
        return {key: value for key, value in parsed.items() if not key.startswith("$")}
    return {}


def _schema_name(raw_schema: str) -> str:
    if not raw_schema or raw_schema == "{}":
        return ""
    try:
        parsed = json.loads(raw_schema)
    except Exception:
        return ""
    if isinstance(parsed, dict):
        title = parsed.get("title") or parsed.get("$ref", "").split("/")[-1]
        return str(title) if title else ""
    return ""


def _schema_model_name(schema: Optional[Any]) -> str:
    return getattr(schema, "name", "") if schema else ""


def _default_status_codes(method: str) -> List[int]:
    return [201, 400, 401] if method.upper() == "POST" else [200, 400, 401]


def _split_endpoint_label(label: str) -> Tuple[str, str]:
    parts = (label or "").split(maxsplit=1)
    if len(parts) == 2:
        return parts[0].upper(), parts[1]
    return "GET", label or ""


def _api_key(method: str, endpoint: str) -> str:
    return f"{(method or '').upper()} {endpoint or ''}"


def _component_for_page(plan, page_name: str) -> str:
    for page in getattr(plan, "pages", []) or []:
        if page.name == page_name and page.components:
            return page.components[0]
    return ""


def _function_name(method: str, endpoint: str) -> str:
    parts = [part for part in endpoint.strip("/").split("/") if part and not part.startswith("{")]
    stem = parts[-1] if parts else "api"
    prefix = {"GET": "get", "POST": "create", "PUT": "update", "PATCH": "update", "DELETE": "delete"}.get(method.upper(), "call")
    return prefix + "".join(part.capitalize() for part in stem.replace("-", "_").split("_"))


def _match_database_entity(api: Optional[APIContract], entities: List[DatabaseEntityContract]) -> Optional[DatabaseEntityContract]:
    if not api:
        return None
    endpoint = api.endpoint.lower()
    purpose = api.purpose.lower()
    for entity in entities:
        tokens = {entity.name.lower(), entity.table.lower(), entity.name.lower() + "s"}
        if any(token and (token in endpoint or token in purpose) for token in tokens):
            return entity
    return None


def _field_mappings(api: Optional[APIContract], db: Optional[DatabaseEntityContract]) -> Dict[str, str]:
    if not api or not db:
        return {}
    fields = set()
    if api.request_body:
        fields.update(api.request_body.fields.keys())
    if api.response_body:
        fields.update(api.response_body.fields.keys())
    db_fields = {field.split(":")[0].strip(): field for field in db.fields}
    return {field: db_fields[field] for field in fields if field in db_fields}


def _endpoint_suggests_persistence(endpoint: str) -> bool:
    return any(part for part in endpoint.strip("/").split("/") if part not in ("api", "auth", "login", "logout", "search", "health"))


def _table_name(name: str) -> str:
    if not name:
        return ""
    lowered = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
    return lowered if lowered.endswith("s") else f"{lowered}s"


def _matching_trace(trace_items, usage: FrontendAPIUsage):
    for item in trace_items:
        if getattr(item, "page", "") == usage.frontend_page:
            return item
    return None


def _issue(category, severity, source, target, file, endpoint, field, expected, actual, description, suggested_fix) -> ContractIssue:
    issue_id = f"CI-{abs(hash((category, source, target, endpoint, field, expected, actual))) % 100000:05d}"
    return ContractIssue(
        issue_id=issue_id,
        category=category,
        severity=severity,
        source=source,
        target=target,
        file=file,
        endpoint=endpoint,
        field=field,
        expected=expected,
        actual=actual,
        description=description,
        suggested_fix=suggested_fix,
    )

