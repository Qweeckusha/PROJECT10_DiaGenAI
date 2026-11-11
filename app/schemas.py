from pydantic import BaseModel, Field
from typing import List, Literal

class BPMNElement(BaseModel):
    """Один элемент BPMN-диаграммы"""
    id: str = Field(..., description="Уникальный идентификатор элемента")
    type: Literal["startEvent", "task", "endEvent"] = Field(
        ...,
        description="Тип элемента: startEvent, task или endEvent"
    )
    name: str = Field(..., description="Название элемента (отображается на диаграмме)")

class BPMNFlow(BaseModel):
    """Связь между двумя элементами BPMN"""
    id: str = Field(..., description="Уникальный идентификатор связи")
    source: str = Field(..., description="ID элемента-источника")
    target: str = Field(..., description="ID элемента-цели")

class BPMNProcess(BaseModel):
    """Полная структура BPMN-процесса, которую генерирует LLM"""
    process_name: str = Field(..., description="Название бизнес-процесса")
    elements: List[BPMNElement] = Field(..., description="Список элементов процесса")
    flows: List[BPMNFlow] = Field(..., description="Список связей между элементами")