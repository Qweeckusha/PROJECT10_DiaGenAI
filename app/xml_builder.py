from lxml import etree
from .schemas import BPMNProcess


def build_bpmn_xml(process: BPMNProcess) -> str:
    """
    Конвертирует структуру BPMNProcess в валидный BPMN 2.0 XML
    """
    # 1. Объявляем неймспейсы ("фамилии" для тегов)
    nsmap = {
        'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
        'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI',
        'dc': 'http://www.omg.org/spec/DD/20100524/DC',
        'di': 'http://www.omg.org/spec/DD/20100524/DI'
    }

    # 2. Создаем корень и процесс
    definitions = etree.Element('{http://www.omg.org/spec/BPMN/20100524/MODEL}definitions', nsmap=nsmap)
    definitions.set('id', 'Definitions_1')
    definitions.set('targetNamespace', 'http://bpmn.io/schema/bpmn')

    bpmn_process = etree.SubElement(definitions, '{http://www.omg.org/spec/BPMN/20100524/MODEL}process')
    bpmn_process.set('id', 'Process_1')
    bpmn_process.set('isExecutable', 'false')

    # 3. Словарь для хранения координат (нужен для рисования стрелок)
    element_coords = {}
    x_position = 152
    y_position = 102

    # Добавляем элементы и запоминаем их координаты
    for element in process.elements:
        tag = f'{{http://www.omg.org/spec/BPMN/20100524/MODEL}}{element.type}'
        xml_element = etree.SubElement(bpmn_process, tag)
        xml_element.set('id', element.id)
        xml_element.set('name', element.name)

        # Определяем размеры в зависимости от типа
        if element.type in ['startEvent', 'endEvent']:
            width, height = 36, 36
        else:  # task
            width, height = 100, 80

        element_coords[element.id] = {'x': x_position, 'y': y_position, 'width': width, 'height': height}
        x_position += 150  # Сдвиг вправо для следующего элемента

    # Добавляем логические связи (без визуала пока)
    for flow in process.flows:
        flow_element = etree.SubElement(
            bpmn_process,
            '{http://www.omg.org/spec/BPMN/20100524/MODEL}sequenceFlow'
        )
        flow_element.set('id', flow.id)
        flow_element.set('sourceRef', flow.source)
        flow_element.set('targetRef', flow.target)

    # 4. Создаем визуальное представление (DI)
    diagram = etree.SubElement(definitions, '{http://www.omg.org/spec/BPMN/20100524/DI}BPMNDiagram')
    diagram.set('id', 'BPMNDiagram_1')

    plane = etree.SubElement(diagram, '{http://www.omg.org/spec/BPMN/20100524/DI}BPMNPlane')
    plane.set('id', 'BPMNPlane_1')
    plane.set('bpmnElement', 'Process_1')

    # Рисуем блоки (Shapes)
    for elem_id, coords in element_coords.items():
        shape = etree.SubElement(plane, '{http://www.omg.org/spec/BPMN/20100524/DI}BPMNShape')
        shape.set('id', f'{elem_id}_di')
        shape.set('bpmnElement', elem_id)

        bounds = etree.SubElement(shape, '{http://www.omg.org/spec/DD/20100524/DC}Bounds')
        bounds.set('x', str(coords['x']))
        bounds.set('y', str(coords['y']))
        bounds.set('width', str(coords['width']))
        bounds.set('height', str(coords['height']))

    # Рисуем стрелки (Edges)
    for flow in process.flows:
        source = element_coords.get(flow.source)
        target = element_coords.get(flow.target)

        # Если оба элемента найдены, рисуем стрелку между ними
        if source and target:
            edge = etree.SubElement(plane, '{http://www.omg.org/spec/BPMN/20100524/DI}BPMNEdge')
            edge.set('id', f'{flow.id}_di')
            edge.set('bpmnElement', flow.id)

            # Точка начала: правый центр элемента-источника
            start_x = source['x'] + source['width']
            start_y = source['y'] + (source['height'] / 2)

            # Точка конца: левый центр элемента-цели
            end_x = target['x']
            end_y = target['y'] + (target['height'] / 2)

            wp1 = etree.SubElement(edge, '{http://www.omg.org/spec/DD/20100524/DI}waypoint')
            wp1.set('x', str(start_x))
            wp1.set('y', str(start_y))

            wp2 = etree.SubElement(edge, '{http://www.omg.org/spec/DD/20100524/DI}waypoint')
            wp2.set('x', str(end_x))
            wp2.set('y', str(end_y))

    # 5. Превращаем дерево в строку
    xml_string = etree.tostring(definitions, pretty_print=True, encoding='unicode')
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_string}'