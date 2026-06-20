from order_service.infrastructure.config import settings


def configure_tracing(app) -> None:
    if settings.app_env != "local":
        return
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)
    except ImportError:
        return
