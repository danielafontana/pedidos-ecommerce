from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = (
        "postgresql+asyncpg://orders_user:orders_pass@localhost:5432/orders_db"
    )
    customer_service_url: str = "http://localhost:8080/customers"
    catalog_service_url: str = "http://localhost:8080/products"
    payment_gateway_url: str = "http://localhost:8080/payments"
    notification_service_url: str = "http://localhost:8080/notifications"
    aws_endpoint_url: str = "http://localhost:4566"
    aws_region: str = "us-east-1"
    aws_access_key_id: str = "test"
    aws_secret_access_key: str = "test"
    sqs_order_events_queue: str = "order-events"
    sqs_saga_commands_queue: str = "saga-commands"
    sqs_notification_dispatch_queue: str = "notification-dispatch"
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    log_level: str = "INFO"
    app_env: str = "local"


settings = Settings()
