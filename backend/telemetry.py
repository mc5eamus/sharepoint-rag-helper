import logging
import os

from azure.core.settings import settings
from azure.core.tracing.ext.opentelemetry_span import OpenTelemetrySpan
from azure.monitor.opentelemetry import configure_azure_monitor

SERVICE_NAME = "rag-backend"

def get_logger():
    return logging.getLogger(SERVICE_NAME)

def setup_telemetry():

    application_insights_connection_string = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")

    if application_insights_connection_string:

        settings.tracing_implementation = OpenTelemetrySpan
        configure_azure_monitor(
            connection_string=application_insights_connection_string,
            logger_name=SERVICE_NAME,
        )


    log = logging.getLogger(SERVICE_NAME)
    log.setLevel(logging.INFO)
