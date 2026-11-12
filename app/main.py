import httpx
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, ValidationError

from .llm import generate_process
from .xml_builder import build_bpmn_xml

app = FastAPI(title="BPMN AI Generator")


class ProcessRequest(BaseModel):
    description: str


@app.post("/generate-bpmn")
async def generate_bpmn(request: ProcessRequest):
    """
    Генерирует BPMN 2.0 XML из текстового описания бизнес-процесса.

    :param request: Текстовое описание процесса
    :return: Валидный BPMN 2.0 XML
    """
    try:
        process = await generate_process(request.description)
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Ollama недоступна")
    except ValidationError:
        raise HTTPException(status_code=502, detail="Модель вернула некорректную структуру")

    bpmn_xml = build_bpmn_xml(process)
    return Response(content=bpmn_xml, media_type="application/xml")


@app.get("/health")
async def health():
    return {"status": "ok"}