"""Añade un diseño vertical de 324 px sin modificar el diseño de escritorio."""
import copy
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainerMobileState/2.9.0/schema.json'

def literal(value):
    if isinstance(value, bool): value = str(value).lower()
    elif isinstance(value, str): value = "'" + value.replace("'", "''") + "'"
    # Las propiedades de tipografía esperan literales DAX Decimal (p. ej. 10D).
    # Sin el sufijo, Desktop descarta el tamaño y utiliza el tema móvil.
    else: value = f'{value}D'
    return {'expr': {'Literal': {'Value': value}}}

def text_content(visual):
    paragraphs = visual['visual'].get('objects', {}).get('general', [{}])[0].get('properties', {}).get('paragraphs', [])
    return '\n'.join(''.join(run.get('value', '') for run in p.get('textRuns', [])) for p in paragraphs)

def generate_mobile_files(files):
    """files es un mapa de rutas PBIR a objetos JSON, con los visuales existentes."""
    additions = {}
    pages = sorted(p for p in files if p.endswith('/page.json'))
    for page_path in pages:
        prefix = page_path.rsplit('/', 1)[0] + '/visuals/'
        visuals = [(p, v) for p, v in files.items() if p.startswith(prefix) and p.endswith('/visual.json')]
        visuals.sort(key=lambda item: (item[1]['position']['y'], item[1]['position']['x']))
        cards = [(p,v) for p,v in visuals if v['visual']['visualType'] == 'card']
        slicers = [(p,v) for p,v in visuals if v['visual']['visualType'] == 'slicer']
        texts = [(p,v) for p,v in visuals if v['visual']['visualType'] == 'textbox']
        charts = [(p,v) for p,v in visuals if v['visual']['visualType'] not in ('textbox','card','slicer','tableEx')]
        tables = [(p,v) for p,v in visuals if v['visual']['visualType'] == 'tableEx']
        index = 0
        rectangles = []

        def place(item, x, y, width, height, font=None, title=None):
            nonlocal index
            path, v = item
            index += 1
            kind = v['visual']['visualType']
            mobile = {'$schema': SCHEMA, 'position':dict(x=x,y=y,z=index,tabOrder=index,width=width,height=height)}
            objects = {}
            container = {'visualHeader':[{'properties':{'show':literal(False)}}],
                         'subTitle':[{'properties':{'show':literal(False)}}]}
            if kind != 'textbox':
                props = {'fontSize':literal(10 if kind == 'card' else 12), 'fontFamily':literal('Segoe UI Semibold')}
                if title: props['text'] = literal(title)
                container['title'] = [{'properties':props}]
            if kind == 'textbox':
                paragraphs = copy.deepcopy(v['visual'].get('objects',{}).get('general',[{}])[0].get('properties',{}).get('paragraphs',[]))
                if title is not None:
                    style = copy.deepcopy(paragraphs[0]['textRuns'][0].get('textStyle',{}))
                    paragraphs = [{'textRuns':[{'value': title, 'textStyle':style}]}]
                for paragraph in paragraphs:
                    for run in paragraph.get('textRuns',[]):
                        run.setdefault('textStyle', {})['fontSize'] = f'{font or 11}pt'
                objects['general'] = [{'properties':{'paragraphs':paragraphs}}]
            elif kind == 'card':
                projections = v['visual'].get('query',{}).get('queryState',{}).get('Values',{}).get('projections',[])
                is_currency = any('COP' in p.get('queryRef','') for p in projections)
                objects['labels'] = [{'properties':{'fontSize':literal(16 if is_currency else 22),'fontFamily':literal('Segoe UI Semibold')}}]
                objects['categoryLabels'] = [{'properties':{'show':literal(False)}}]
            elif kind == 'slicer':
                objects['header'] = [{'properties':{'textSize':literal(10)}}]
                objects['items'] = [{'properties':{'textSize':literal(11)}}]
            elif kind == 'tableEx':
                objects['grid'] = [{'properties':{'textSize':literal(10)}}]
                objects['columnHeaders'] = [{'properties':{'fontSize':literal(10),'wordWrap':literal(True)}}]
            else:
                objects['categoryAxis'] = [{'properties':{'fontSize':literal(9),'showAxisTitle':literal(False)}}]
                objects['valueAxis'] = [{'properties':{'fontSize':literal(9),'showAxisTitle':literal(False)}}]
                objects['legend'] = [{'properties':{'fontSize':literal(9)}}]
            mobile['objects'] = objects
            mobile['visualContainerObjects'] = container
            additions[path.replace('/visual.json','/mobile.json')] = mobile
            rectangles.append(mobile['position'])

        # Identifica los textos por posición, no por GUID, y conserva sus colores.
        brand = next(t for t in texts if t[1]['position']['y'] == 14)
        heading = next(t for t in texts if t[1]['position']['y'] == 44)
        subtitle = next(t for t in texts if t[1]['position']['y'] == 90)
        footer = next(t for t in texts if t[1]['position']['y'] == 752)
        place(brand,0,0,324,30,10,'MPS | SUPPLY CHAIN & SALES')
        place(heading,0,30,324,64,18)
        place(subtitle,0,102,324,64,10)
        for i,item in enumerate(slicers): place(item,166*i,174,158,64)
        for i,item in enumerate(cards): place(item,166*(i%2),246+120*(i//2),158,112)
        y = 246 + 120*((len(cards)+1)//2)
        # En pronósticos se presenta primero la proyección futura y luego el histórico.
        if files[page_path]['displayName'] == 'Pronósticos':
            charts.sort(key=lambda item: item[1]['visual']['visualType'] != 'clusteredColumnChart')
        for item in charts:
            is_line = item[1]['visual']['visualType'] == 'lineChart'
            height = 280 if is_line else 252
            title = None
            if files[page_path]['displayName'] == 'Pronósticos':
                title = 'Demanda real y media móvil' if is_line else 'Proyección: próximos 3 meses'
            place(item,0,y,324,height,title=title)
            y += height + 12
        for item in tables:
            title = {'Productos e inventario':'Stock y cobertura por referencia',
                     'Importaciones':'Detalle de proveedores',
                     'Pronósticos':'Proyección por categoría',
                     'Indicadores de gestión':'Indicadores por categoría'}.get(files[page_path]['displayName'])
            place(item,0,y,324,330,title=title)
            y += 342
        for item in texts:
            if item in (brand,heading,subtitle,footer): continue
            height = 220 if text_content(item[1]).startswith('NIVEL DE SERVICIO') else 340
            place(item,0,y,324,height,11)
            y += height + 12
        footer_height = 152
        place(footer,0,y,324,footer_height,10)
        # Verifica tamaños, límites horizontales y ausencia de superposiciones.
        for i,a in enumerate(rectangles):
            assert a['x'] >= 0 and a['x']+a['width'] <= 324
            assert a['y'] >= 0 and a['width'] > 0 and a['height'] > 0
            for b in rectangles[i+1:]:
                overlap = a['x'] < b['x']+b['width'] and b['x'] < a['x']+a['width'] and a['y'] < b['y']+b['height'] and b['y'] < a['y']+a['height']
                assert not overlap, (page_path,a,b)
        assert len(rectangles) == len(visuals), (page_path, 'Visual sin diseño móvil')
        print(f"{files[page_path]['displayName']}: {len(rectangles)} visuales, 324 × {y+footer_height} px")
    return additions

def update_pbix(path):
    temporary = path.with_name(path.stem + '.movil.tmp.pbix')
    with zipfile.ZipFile(path) as src:
        files = {n:json.loads(src.read(n)) for n in src.namelist() if n.startswith('Report/definition/pages/') and (n.endswith('/page.json') or n.endswith('/visual.json'))}
        additions = generate_mobile_files(files)
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as dst:
            for entry in src.infolist():
                if entry.filename.endswith('/mobile.json') or entry.filename == 'SecurityBindings': continue
                dst.writestr(entry,src.read(entry.filename))
            for name,value in additions.items(): dst.writestr(name,json.dumps(value,ensure_ascii=False,separators=(',',':')))
    with zipfile.ZipFile(temporary) as check:
        assert check.testzip() is None
        assert len([n for n in check.namelist() if n.endswith('/mobile.json')]) == len(additions)
    temporary.replace(path)

if __name__ == '__main__':
    update_pbix(ROOT/'MPS Supply Chain - Informe.pbix')
