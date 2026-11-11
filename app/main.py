

from fastapi import FastAPI
from pydantic import BaseModel

from .schemas import BPMNProcess, BPMNElement, BPMNFlow
from .xml_builder import build_bpmn_xml



app = FastAPI(title="BPMN AI Generator")


# IN
class ProcessRequest(BaseModel):
    description: str


# OUT
class ProcessResponse(BaseModel):
    bpmn_xml: str
    status: str


@app.post("/generate-bpmn", response_model=ProcessResponse)
async def generate_bpmn(request: ProcessRequest):
    """
    Эндпоинт принимает текстовое описание бизнес-процесса
    и возвращает валидный XML и статус
    """

    test_process = BPMNProcess(
        process_name="Тестовый процесс",
        elements=[
            BPMNElement(id="start_1", type="startEvent", name="Начало"),
            BPMNElement(id="task_1", type="task", name="Тестовая задача"),
            BPMNElement(id="end_1", type="endEvent", name="Конец")
        ],
        flows=[
            BPMNFlow(id="flow_1", source="start_1", target="task_1"),
            BPMNFlow(id="flow_2", source="task_1", target="end_1")
        ]
    )

    # Конвертируем в XML
    bpmn_xml = build_bpmn_xml(test_process)

    return ProcessResponse(bpmn_xml=bpmn_xml, status="success")

@app.get("/health")
async def health():
    return {"status": "ok"}