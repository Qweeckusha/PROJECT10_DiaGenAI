import httpx
from cfg import MODEL, URL, SYSTEM_PROMPT
from app.schemas import BPMNProcess


TIMEOUT = 120.0


async def generate_process(description: str) -> BPMNProcess:
    """
    Отправляет описание процесса в Ollama и возвращает структурированный BPMNProcess.

    :param description: Текстовое описание бизнес-процесса
    :return: Структура BPMN-процесса
    """
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": description},
        ],
        "stream": False,
        "format": BPMNProcess.model_json_schema(),
        "think": False,
        "options": {"temperature": 0.1},
    }

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(f"{URL}/api/chat", json=payload)
        response.raise_for_status()

    return BPMNProcess.model_validate_json(response.json()["message"]["content"])