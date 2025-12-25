import os
import requests
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

def setup_tracing(service_name: str) -> None:
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://simplest-collector:4317")

    provider = TracerProvider(
        resource=Resource.create({"service.name": service_name})
    )
    exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)

app = FastAPI(title="Order Service")

setup_tracing("order-service")
FastAPIInstrumentor.instrument_app(app)
RequestsInstrumentor().instrument()

PRICING_SERVICE_URL = os.getenv("PRICING_SERVICE_URL", "http://service-b:8080")

@app.get("/orders/{order_id}/price")
def get_order_price(order_id: str):
    tracer = trace.get_tracer(__name__)

    # допустим, сложность модели мы получили из БД
    model_complexity = 3

    with tracer.start_as_current_span("get_order_price") as span:
        span.set_attribute("order.id", order_id)
        span.set_attribute("model.complexity", model_complexity)

        response = requests.get(
            f"{PRICING_SERVICE_URL}/calculate",
            params={
                "order_id": order_id,
                "complexity": model_complexity,
            },
            timeout=5,
        )

        return {
            "order_id": order_id,
            "price": response.json(),
        }