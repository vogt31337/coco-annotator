import os
import logging
import backend.config as Config
from backend.webserver.variables import responses

from backend.webserver.api import admin, categories

from fastapi import FastAPI, HTTPException, Response
from fastapi.openapi.docs import get_swagger_ui_html

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(admin.router)
app.include_router(categories.router)
app.include_router(network_statistic.router)
app.include_router(outage_analysis.router)
app.include_router(voltage_statistic.router)

@app.get("/docs", responses=responses)
async def read_docs():
    return Response(content=get_swagger_ui_html(
        title="api docs",
        openapi_url="/openapi.json"
    ), media_type="text/html")


@app.get("/", responses=responses)
async def ready():
    if Config.DEBUG:
        return os.environ
    return "Hello World!"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=Config.REST_IP, port=int(Config.REST_PORT))
