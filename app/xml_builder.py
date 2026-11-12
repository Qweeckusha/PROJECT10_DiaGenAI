from lxml import etree
from .schemas import BPMNProcess

# URI пространств имён для цветов bpmn-js
BIOC_NS = 'http://bpmn.io/schema/bpmn/biocolor/1.0'
COLOR_NS = 'http://www.omg.org/spec/BPMN/non-normative/color/1.0'


def build_bpmn_xml(process: BPMNProcess) -> str:
    """
    Конвертирует структуру BPMNProcess в валидный BPMN 2.0 XML
    с идеальным центрированием и ортогональной маршрутизацией.
    """
    nsmap = {
        'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
        'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI',
        'dc': 'http://www.omg.org/spec/DD/20100524/DC',
        'di': 'http://www.omg.org/spec/DD/20100524/DI',
        'bioc': BIOC_NS,
        'color': COLOR_NS
    }

    definitions = etree.Element(
        '{http://www.omg.org/spec/BPMN/20100524/MODEL}definitions', nsmap=nsmap
    )
    definitions.set('id', 'Definitions_1')
    definitions.set('targetNamespace', 'http://bpmn.io/schema/bpmn')

    bpmn_process = etree.SubElement(
        definitions, '{http://www.omg.org/spec/BPMN/20100524/MODEL}process'
    )
    bpmn_process.set('id', 'Process_1')
    bpmn_process.set('isExecutable', 'false')

    # --- 1. Анализ структуры для ветвлений ---
    gateway_ids = {e.id for e in process.elements if 'Gateway' in e.type}
    branches = {}
    current_branch = None

    for element in process.elements:
        if element.id in gateway_ids:
            current_branch = element.id
            branches[current_branch] = []
        elif current_branch:
            for flow in process.flows:
                if flow.source == current_branch and flow.target == element.id:
                    branches[current_branch].append(element.id)
                    break

    # --- 2. Расчёт координат с идеальным центрированием ---
    element_coords = {}
    x_step = 220
    center_y = 150  # Единая горизонтальная ось для основного потока
    branch_spacing = 120  # Расстояние между ветками по вертикали
    x_position = 152

    for element in process.elements:
        tag = f'{{http://www.omg.org/spec/BPMN/20100524/MODEL}}{element.type}'
        xml_element = etree.SubElement(bpmn_process, tag)
        xml_element.set('id', element.id)
        xml_element.set('name', element.name)

        if element.type in ['startEvent', 'endEvent']:
            width, height = 36, 36
        elif 'Gateway' in element.type:
            width, height = 50, 50
        else:
            width, height = 100, 80

        # Определяем центральную ось для текущего элемента
        current_center_y = center_y
        if element.id not in gateway_ids:
            for gw_id, branch_elements in branches.items():
                if element.id in branch_elements:
                    branch_idx = branch_elements.index(element.id)
                    # Чётные ветки идут вверх, нечётные вниз
                    current_center_y = (
                        center_y - branch_spacing
                        if branch_idx % 2 == 0
                        else center_y + branch_spacing
                    )
                    break

        # МАГИЯ ЦЕНТРИРОВАНИЯ: y = центр_оси - (половина_высоты)
        y_position = current_center_y - (height / 2)

        element_coords[element.id] = {
            'x': x_position,
            'y': y_position,
            'width': width,
            'height': height,
            'center_y': current_center_y  # Сохраняем для расчёта стрелок
        }
        x_position += x_step

    # --- 3. Логические связи ---
    for flow in process.flows:
        flow_element = etree.SubElement(
            bpmn_process, '{http://www.omg.org/spec/BPMN/20100524/MODEL}sequenceFlow'
        )
        flow_element.set('id', flow.id)
        flow_element.set('sourceRef', flow.source)
        flow_element.set('targetRef', flow.target)

        if flow.condition:
            condition_expr = etree.SubElement(
                flow_element,
                '{http://www.omg.org/spec/BPMN/20100524/MODEL}conditionExpression'
            )
            condition_expr.text = flow.condition

    # --- 4. Визуальная часть (DI) и цвета ---
    diagram = etree.SubElement(
        definitions, '{http://www.omg.org/spec/BPMN/20100524/DI}BPMNDiagram'
    )
    diagram.set('id', 'BPMNDiagram_1')

    plane = etree.SubElement(
        diagram, '{http://www.omg.org/spec/BPMN/20100524/DI}BPMNPlane'
    )
    plane.set('id', 'BPMNPlane_1')
    plane.set('bpmnElement', 'Process_1')

    color_map = {
        'startEvent': {'fill': '#c8e6c9', 'stroke': '#205022'},
        'endEvent': {'fill': '#ffcdd2', 'stroke': '#831311'},
        'exclusiveGateway': {'fill': '#ffe0b2', 'stroke': '#6b3c00'},
        'parallelGateway': {'fill': '#ffe0b2', 'stroke': '#6b3c00'},
        'inclusiveGateway': {'fill': '#ffe0b2', 'stroke': '#6b3c00'},
        'task': {'fill': '#bbdefb', 'stroke': '#0d4372'}
    }

    for elem_id, coords in element_coords.items():
        element = next(e for e in process.elements if e.id == elem_id)
        colors = color_map.get(element.type, color_map['task'])

        shape = etree.SubElement(
            plane, '{http://www.omg.org/spec/BPMN/20100524/DI}BPMNShape'
        )
        shape.set('id', f'{elem_id}_di')
        shape.set('bpmnElement', elem_id)
        shape.set(f'{{{BIOC_NS}}}fill', colors['fill'])
        shape.set(f'{{{BIOC_NS}}}stroke', colors['stroke'])
        shape.set(f'{{{COLOR_NS}}}background-color', colors['fill'])
        shape.set(f'{{{COLOR_NS}}}border-color', colors['stroke'])

        bounds = etree.SubElement(
            shape, '{http://www.omg.org/spec/DD/20100524/DC}Bounds'
        )
        bounds.set('x', str(coords['x']))
        bounds.set('y', str(coords['y']))
        bounds.set('width', str(coords['width']))
        bounds.set('height', str(coords['height']))

    # --- 5. Умная маршрутизация стрелок ---
    # Словарь исходящих потоков для каждого шлюза
    gateway_outgoing = {
        gw_id: [f for f in process.flows if f.source == gw_id]
        for gw_id in gateway_ids
    }

    for flow in process.flows:
        source = element_coords[flow.source]
        target = element_coords[flow.target]
        source_elem = next((e for e in process.elements if e.id == flow.source), None)

        edge = etree.SubElement(
            plane, '{http://www.omg.org/spec/BPMN/20100524/DI}BPMNEdge'
        )
        edge.set('id', f'{flow.id}_di')
        edge.set('bpmnElement', flow.id)

        waypoints = []

        if source_elem and 'Gateway' in source_elem.type:
            # ЛОГИКА ДЛЯ ШЛЮЗОВ: 1 изгиб, выход сверху/снизу
            flows_from_gw = gateway_outgoing[flow.source]
            flow_idx = flows_from_gw.index(flow)
            center_x = source['x'] + (source['width'] / 2)

            if flow_idx == 0:
                # Первая ветка: выход СВЕРХУ
                start_y = source['y']
            else:
                # Вторая ветка: выход СНИЗУ
                start_y = source['y'] + source['height']

            # Строим Г-образную линию: вертикально до уровня цели, затем горизонтально
            waypoints.append((center_x, start_y))
            waypoints.append((center_x, target['center_y']))  # Тот самый 1 изгиб!
            waypoints.append((target['x'], target['center_y']))

        else:
            # ЛОГИКА ДЛЯ ОБЫЧНЫХ ЭЛЕМЕНТОВ: ортогональная маршрутизация
            start_x = source['x'] + source['width']
            start_y = source['center_y']
            end_x = target['x']
            end_y = target['center_y']

            waypoints.append((start_x, start_y))

            # Если есть вертикальное смещение, добавляем изгиб
            if abs(start_y - end_y) > 5:
                mid_x = start_x + 50 if end_x > start_x else end_x - 50
                waypoints.append((mid_x, start_y))
                waypoints.append((mid_x, end_y))

            waypoints.append((end_x, end_y))

        # Записывем точки в XML
        for wx, wy in waypoints:
            wp = etree.SubElement(
                edge, '{http://www.omg.org/spec/DD/20100524/DI}waypoint'
            )
            wp.set('x', str(wx))
            wp.set('y', str(wy))

    xml_string = etree.tostring(definitions, pretty_print=True, encoding='unicode')
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_string}'