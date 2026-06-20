from prometheus_client import make_asgi_app


def create_metrics_app():
    return make_asgi_app()
