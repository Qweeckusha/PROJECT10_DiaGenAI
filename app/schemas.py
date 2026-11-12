from pydantic import BaseModel, Field, model_validator
from typing import List, Literal


class BPMNElement(BaseModel):

    """Элемент BPMN-диаграммы"""

    id: str
    type: Literal["startEvent", "task", "endEvent", "exclusiveGateway", "parallelGateway", "inclusiveGateway"]
    name: str


class BPMNFlow(BaseModel):

    """Связь между элементами BPMN"""

    id: str
    source: str
    target: str
    condition: str | None = None


class BPMNProcess(BaseModel):

    """Структура BPMN-процесса"""

    process_name: str
    elements: List[BPMNElement]
    flows: List[BPMNFlow]

    @model_validator(mode="after")
    def check_integrity(self) -> "BPMNProcess":

        """Проверяет уникальность id и целостность связей"""

        ids = [e.id for e in self.elements]
        if len(ids) != len(set(ids)):
            raise ValueError("id элементов должны быть уникальны")

        known = set(ids)

        for flow in self.flows:
            if flow.source not in known or flow.target not in known:
                raise ValueError(f"Связь {flow.id} ссылается на несуществующий элемент")

        gateway_ids = {e.id for e in self.elements if "Gateway" in e.type}
        for gw_id in gateway_ids:
            outgoing = [f for f in self.flows if f.source == gw_id]
            incoming = [f for f in self.flows if f.target == gw_id]
            if len(outgoing) < 2 and len(incoming) < 2:
                raise ValueError(f"Gateway {gw_id} должен иметь минимум 2 потока")

        return self