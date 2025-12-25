import os
import time
from fastapi import FastAPI, Query
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

def setup_tracing(service_name: str) -> None:
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://simplest-collector:4317")
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

app = FastAPI(title="Pricing Service")

setup_tracing("pricing-service")
FastAPIInstrumentor.instrument_app(app)

@app.get("/calculate")
def calculate(
    order_id: str = Query(...),
    complexity: int = Query(3, ge=1, le=10),
):
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("calculate_price") as span:
        span.set_attribute("order.id", order_id)
        span.set_attribute("model.complexity", complexity)

        time.sleep(0.2)  # имитация расчёта
        price = 1000 + complexity * 500

        span.set_attribute("price.value", price)
        return {"order_id": order_id, "price": price, "currency": "RUB"}