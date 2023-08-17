import os
import weaviate  # type: ignore[import]

from wasabi import msg  # type: ignore[import]

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dotenv import load_dotenv

from SimpleVerbaEngine import SimpleVerbaQueryEngine

load_dotenv()

verba_engine = SimpleVerbaQueryEngine(
    os.environ.get("WEAVIATE_URL", ""),
    os.environ.get("WEAVIATE_API_KEY", ""),
    os.environ.get("OPENAI_API_KEY", ""),
)

msg.good("Connected to Weaviate Client")

# FastAPI App
app = FastAPI()

origins = ["http://localhost:3000"]

# Add middleware for handling Cross Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryPayload(BaseModel):
    query: str


class GetDocumentPayload(BaseModel):
    document_id: str


# Define health check endpoint
@app.get("/health")
async def root():
    try:
        if verba_engine.get_client().is_ready():
            return JSONResponse(
                content={
                    "message": "Alive!",
                }
            )
        else:
            return JSONResponse(
                content={
                    "message": "Database not ready!",
                },
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
    except Exception as e:
        msg.fail(f"Healthcheck failed with {str(e)}")
        return JSONResponse(
            content={
                "message": f"Healthcheck failed with {str(e)}",
            },
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


@app.post("/query")
async def query(payload: QueryPayload):
    try:
        system_msg, results = verba_engine.query(payload.query)
        msg.good(f"Succesfully processed query: {payload.query}")

        return JSONResponse(
            content={
                "system": system_msg,
                "documents": results,
            }
        )
    except Exception as e:
        msg.fail(f"Query failed: {str(e)}")
        return JSONResponse(
            content={
                "system": f"Something went wrong! {str(e)}",
                "documents": [],
            }
        )


@app.post("/get_document")
async def get_document(payload: GetDocumentPayload):
    msg.info(f"Document ID received: {payload.document_id}")

    try:
        document = verba_engine.retrieve_document(payload.document_id)
        msg.good(f"Succesfully retrieved document: {payload.document_id}")
        return JSONResponse(
            content={
                "document": document,
            }
        )
    except Exception as e:
        msg.fail(f"Query failed: {str(e)}")
        return JSONResponse(
            content={
                "document": {},
            }
        )
