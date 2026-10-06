def get_model_compat(model_router, task_type: str):
    try:
        return model_router.get_model(task_type)
    except TypeError as exc:
        message = str(exc)
        if "positional" not in message and "argument" not in message:
            raise
        return model_router.get_model()


def active_model_name(model_router, task_type: str):
    return getattr(model_router, "active_models", {}).get(task_type, {}).get("actual")
