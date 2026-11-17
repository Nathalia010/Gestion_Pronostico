"""Genera las medidas y las cinco páginas PBIR del informe MPS."""
import json, uuid, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEASURES = []
def m(name, expression, fmt='#,0', table='Ventas'):
    MEASURES.append(dict(name=name, expression=expression, format=fmt, table=table))

m('Ventas COP', 'SUM(Ventas[ValorVentaCOP])', '"$" #,0')
m('Unidades vendidas', 'SUM(Ventas[Cantidad])')
m('Transacciones', 'COUNTROWS(Ventas)')
m('Referencias activas', 'CALCULATE(DISTINCTCOUNT(Productos[SKU]), Productos[EstadoReferencia] = "Activa")', table='Productos')
m('Referencias con venta', 'DISTINCTCOUNT(Ventas[SKU])')
m('Ticket promedio COP', 'DIVIDE([Ventas COP], [Transacciones])', '"$" #,0')
m('Corte inventario', 'VAR Limite = MAX(Calendario[Fecha]) RETURN CALCULATE(MAX(Inventario[FechaCorte]), REMOVEFILTERS(Calendario), Inventario[FechaCorte] <= Limite)', 'dd mmm yyyy', 'Inventario')
m('Stock unidades', 'VAR Corte = [Corte inventario] RETURN IF(NOT ISBLANK(Corte), CALCULATE(SUM(Inventario[StockUnidades]), REMOVEFILTERS(Calendario), Inventario[FechaCorte] = Corte))', table='Inventario')
m('Inventario COP', 'VAR Corte = [Corte inventario] RETURN IF(NOT ISBLANK(Corte), CALCULATE(SUM(Inventario[CostoInventarioCOP]), REMOVEFILTERS(Calendario), Inventario[FechaCorte] = Corte))', '"$" #,0', 'Inventario')
m('Stock disponible', 'VAR Corte = [Corte inventario] RETURN IF(NOT ISBLANK(Corte), CALCULATE(SUM(Inventario[StockUnidades]) - SUM(Inventario[StockReservado]), REMOVEFILTERS(Calendario), Inventario[FechaCorte] = Corte))', table='Inventario')
m('Demanda mensual reciente', 'VAR Fin = EOMONTH(CONVERT(CALCULATE(MAX(Ventas[FechaVenta]), REMOVEFILTERS()), DATETIME), 0) VAR Inicio = INT(EOMONTH(Fin, -3)) + 1 RETURN DIVIDE(CALCULATE([Unidades vendidas], REMOVEFILTERS(Calendario), FILTER(ALL(Ventas[FechaVenta]), Ventas[FechaVenta] >= Inicio && Ventas[FechaVenta] <= INT(Fin))), 3)', '#,0')
m('Cobertura dias', 'DIVIDE([Stock disponible], DIVIDE([Demanda mensual reciente], 30))', '0.0', 'Inventario')
m('Referencias sin stock', 'COUNTROWS(FILTER(VALUES(Productos[SKU]), NOT ISBLANK([Stock disponible]) && [Stock disponible] <= 0))', table='Inventario')
m('Referencias en riesgo', 'COUNTROWS(FILTER(VALUES(Productos[SKU]), NOT ISBLANK([Cobertura dias]) && [Cobertura dias] < 30))', table='Inventario')
m('Ordenes importacion', 'COUNTROWS(Importaciones)', table='Importaciones')
m('Unidades ordenadas', 'SUM(Importaciones[CantidadOrdenada])', table='Importaciones')
m('Costo importacion COP', 'SUMX(Importaciones, Importaciones[CantidadOrdenada] * Importaciones[CostoUnitarioImportacionCOP])', '"$" #,0', 'Importaciones')
m('Ordenes recibidas', 'COUNTROWS(FILTER(Importaciones, NOT ISBLANK(Importaciones[FechaRecepcion])))', table='Importaciones')
m('Ordenes pendientes', '[Ordenes importacion] - [Ordenes recibidas]', table='Importaciones')
m('Entrega promedio dias', 'AVERAGEX(FILTER(Importaciones, NOT ISBLANK(Importaciones[FechaRecepcion])), Importaciones[FechaRecepcion] - Importaciones[FechaPedido])', '0.0', 'Importaciones')
m('Entregas a tiempo', 'DIVIDE(COUNTROWS(FILTER(Importaciones, NOT ISBLANK(Importaciones[FechaRecepcion]) && Importaciones[FechaRecepcion] <= Importaciones[FechaEntregaEsperada])), [Ordenes recibidas])', '0.0%', 'Importaciones')
m('Media movil 3 meses', 'VAR Fin = INT(EOMONTH(MAX(Calendario[AñoMes]), -1)) VAR Inicio = INT(EOMONTH(MAX(Calendario[AñoMes]), -4)) + 1 VAR InicioDatos = CALCULATE(MIN(Ventas[FechaVenta]), REMOVEFILTERS()) RETURN IF(Inicio >= InicioDatos, DIVIDE(CALCULATE([Unidades vendidas], REMOVEFILTERS(Calendario), FILTER(ALL(Ventas[FechaVenta]), Ventas[FechaVenta] >= Inicio && Ventas[FechaVenta] <= Fin)), 3))', '#,0')
m('Proyeccion proximo mes', '[Demanda mensual reciente]', '#,0')
m('Mes proyectado', 'FORMAT(EOMONTH(CONVERT(CALCULATE(MAX(Ventas[FechaVenta]), REMOVEFILTERS()), DATETIME), 0) + 1, "mmm yyyy")', '')
m('MAPE prueba 3 meses', 'VAR Ultimo = EOMONTH(CONVERT(CALCULATE(MAX(Ventas[FechaVenta]), REMOVEFILTERS()), DATETIME), 0) RETURN AVERAGEX(GENERATESERIES(0, 2), VAR Fin = INT(EOMONTH(Ultimo, -[Value])) VAR Inicio = INT(EOMONTH(Ultimo, -[Value]-1)) + 1 VAR BaseInicio = INT(EOMONTH(Ultimo, -[Value]-4)) + 1 VAR Real = CALCULATE([Unidades vendidas], REMOVEFILTERS(Calendario), FILTER(ALL(Ventas[FechaVenta]), Ventas[FechaVenta] >= Inicio && Ventas[FechaVenta] <= Fin)) VAR Pred = DIVIDE(CALCULATE([Unidades vendidas], REMOVEFILTERS(Calendario), FILTER(ALL(Ventas[FechaVenta]), Ventas[FechaVenta] >= BaseInicio && Ventas[FechaVenta] < Inicio)), 3) RETURN IF(Real > 0, DIVIDE(ABS(Real - Pred), Real)))', '0.0%')
m('Costo venta estimado', 'SUMX(Ventas, Ventas[Cantidad] * RELATED(Productos[CostoUnitarioCOP]))', '"$" #,0')
m('Inventario medio COP', 'AVERAGEX(VALUES(Inventario[FechaCorte]), CALCULATE(SUM(Inventario[CostoInventarioCOP])))', '"$" #,0', 'Inventario')
m('Rotacion estimada', 'DIVIDE([Costo venta estimado], [Inventario medio COP])', '0.00" x"')
m('Nivel de servicio', '"Sin datos de pedidos"', '')
m('Disponibilidad referencias', 'VAR Total = COUNTROWS(FILTER(VALUES(Productos[SKU]), NOT ISBLANK([Stock disponible]))) RETURN DIVIDE(Total - [Referencias sin stock], Total)', '0.0%', 'Inventario')

schema = 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/'
def lit(value):
    if isinstance(value, bool): value = 'true' if value else 'false'
    elif isinstance(value, str): value = "'" + value.replace("'", "''") + "'"
    else: value = str(value)
    return {'expr': {'Literal': {'Value': value}}}
def color(value): return {'solid': {'color': lit(value)}}
def col(table, name): return {'Column': {'Expression': {'SourceRef': {'Entity': table}}, 'Property': name}}
def measure(name):
    table = next(x['table'] for x in MEASURES if x['name'] == name)
    return {'Measure': {'Expression': {'SourceRef': {'Entity': table}}, 'Property': name}}
def proj(field):
    kind = next(iter(field)); item = field[kind]
    return {'field': field, 'queryRef': item['Expression']['SourceRef']['Entity']+'.'+item['Property'], 'nativeQueryRef': item['Property']}

FILES = {}
PAGE = ''
Z = 0
def visual(kind, x, y, w, h, title=None, roles=None, objects=None, container=None, sort=None):
    global Z
    Z += 1; uid = uuid.uuid4().hex[:20]
    v = {'$schema':schema+'visualContainer/2.14.0/schema.json', 'name':uid,
         'position':dict(x=x,y=y,z=Z,tabOrder=Z,width=w,height=h),
         'visual':{'visualType':kind,'drillFilterOtherVisuals':True}}
    if roles:
        v['visual']['query']={'queryState':{r:{'projections':[proj(f) for f in fs]} for r,fs in roles.items()}}
        if sort: v['visual']['query']['sortDefinition']={'sort':[{'field':sort[0], 'direction':sort[1]}]}
    base = {
        'background':[{'properties':{'show':lit(True),'color':color('#FFFFFF'),'transparency':lit(0)}}],
        'border':[{'properties':{'show':lit(False)}}],
        'visualHeader':[{'properties':{'show':lit(False)}}],
    }
    if title:
        base['title']=[{'properties':{'show':lit(True),'text':lit(title),'fontColor':color('#16324F'),'fontSize':lit(11),'fontFamily':lit('Segoe UI Semibold'),'alignment':lit('left')}}]
    if container: base.update(container)
    v['visual']['visualContainerObjects']=base
    if objects: v['visual']['objects']=objects
    FILES[f'Report/definition/pages/{PAGE}/visuals/{uid}/visual.json']=v
    return v

def text(txt,x,y,w,h,size=12,fg='#526477',bg='#F3F6FA',bold=False):
    visual('textbox',x,y,w,h,objects={
        'general':[{'properties':{'paragraphs':[{'textRuns':[{'value':txt,'textStyle':{'fontFamily':'Segoe UI','fontSize':f'{size}pt','color':fg,'fontWeight':'bold' if bold else 'normal'}}]}]}}]},
        container={'background':[{'properties':{'show':lit(True),'color':color(bg),'transparency':lit(0)}}]})
def card(name,x,label=None):
    visual('card',x,158,296,116,label or name,{'Values':[measure(name)]},objects={
        'labels':[{'properties':{'color':color('#123C5A'),'fontFamily':lit('Segoe UI Semibold'),'fontSize':lit(24),'labelDisplayUnits':lit(0)}}],
        'categoryLabels':[{'properties':{'show':lit(False)}}]})
def chart(title,kind,field,names,x,y,w,h,descending=True):
    roles={'Category':[field], 'Y':[measure(n) for n in names]}
    visual(kind,x,y,w,h,title,roles,objects={'legend':[{'properties':{'show':lit(len(names)>1)}}], 'categoryAxis':[{'properties':{'show':lit(True),'showAxisTitle':lit(False),'fontSize':lit(9)}}]},sort=(measure(names[0]),'Descending') if descending else (field,'Ascending'))
def table(title,fields,x,y,w,h):
    visual('tableEx',x,y,w,h,title,{'Values':fields},objects={'grid':[{'properties':{'textSize':lit(10)}}]})
def page(num,name,subtitle,foot,filters):
    global PAGE,Z
    PAGE=f'mps{num:017d}'; Z=0
    FILES[f'Report/definition/pages/{PAGE}/page.json']={'$schema':schema+'page/2.1.0/schema.json','name':PAGE,'displayName':name,'displayOption':'FitToPage','height':800,'width':1280,'objects':{'background':[{'properties':{'color':color('#F3F6FA'),'transparency':lit(0)}}]}}
    text('MPS  |  SUPPLY CHAIN & SALES ANALYTICS',24,14,1232,30,12,'#71DDD2','#122D45',True)
    text(f'{num:02d}  {name}',24,44,1232,42,24,'#FFFFFF','#122D45',True)
    text(subtitle,24,90,850,30,11)
    for i,(t,c) in enumerate(filters):
        visual('slicer',880+i*188,92,180,54,roles={'Values':[col(t,c)]},objects={'data':[{'properties':{'mode':lit('Dropdown')}}]})
    text(foot,24,752,1232,42,10)
    return PAGE

def build():
    order=[]
    order.append(page(1,'Resumen ejecutivo','Ventas e inventario | Enero 2025 – Octubre 2026 | COP', 'Datos ficticios para portafolio. Inventario: último corte disponible dentro del período seleccionado. Selecciona un gráfico para cruzar filtros.', [('Calendario','Año'),('Calendario','Mes')]))
    for i,(n,l) in enumerate([('Ventas COP','Ventas totales (COP)'),('Unidades vendidas',None),('Referencias activas',None),('Inventario COP','Inventario al corte (COP)')]): card(n,24+312*i,l)
    chart('Evolución mensual de ventas','lineChart',col('Calendario','AñoMes'),['Ventas COP'],24,278,760,245,False)
    chart('Ventas por canal','clusteredBarChart',col('Ventas','Canal'),['Ventas COP'],800,278,456,245)
    chart('Ventas por ciudad','clusteredBarChart',col('Ventas','Ciudad'),['Ventas COP'],24,542,608,190)
    chart('Ventas por categoría','clusteredBarChart',col('Productos','Categoria'),['Ventas COP'],648,542,608,190)
    order.append(page(2,'Productos e inventario','Stock, demanda y cobertura por referencia', 'Riesgo: cobertura menor a 30 días. Cobertura = stock disponible / demanda diaria de los últimos 3 meses del histórico. No se suman cortes.', [('Productos','Categoria'),('Productos','Marca')]))
    for i,n in enumerate(['Stock unidades','Stock disponible','Referencias en riesgo','Referencias sin stock']): card(n,24+312*i)
    chart('Unidades vendidas por categoría','clusteredBarChart',col('Productos','Categoria'),['Unidades vendidas'],24,278,608,220)
    chart('Inventario por categoría (COP)','clusteredBarChart',col('Productos','Categoria'),['Inventario COP'],648,278,608,220)
    table('Referencias: ventas, stock y cobertura (ordena las columnas para detectar productos lentos)',[col('Productos','Referencia'),measure('Unidades vendidas'),measure('Ventas COP'),measure('Stock disponible'),measure('Cobertura dias')],24,518,1232,214)
    order.append(page(3,'Importaciones','Órdenes, costos y desempeño de proveedores | Filtro de tiempo por fecha de pedido', 'Tiempo de entrega y puntualidad: solo órdenes con fecha de recepción. Costos: cantidad ordenada × costo unitario de importación.', [('Calendario','Año'),('Importaciones','EstadoImportacion')]))
    for i,n in enumerate(['Ordenes importacion','Costo importacion COP','Entrega promedio dias','Entregas a tiempo']): card(n,24+312*i)
    chart('Órdenes por estado','clusteredBarChart',col('Importaciones','EstadoImportacion'),['Ordenes importacion'],24,278,608,220)
    chart('Unidades ordenadas por mes','lineChart',col('Calendario','AñoMes'),['Unidades ordenadas'],648,278,608,220,False)
    table('Comparativo de proveedores',[col('Proveedores','Proveedor'),measure('Ordenes importacion'),measure('Ordenes recibidas'),measure('Ordenes pendientes'),measure('Entrega promedio dias'),measure('Entregas a tiempo'),measure('Costo importacion COP')],24,518,1232,214)
    order.append(page(4,'Pronósticos','Modelo base: media móvil de 3 meses | Proyección mensual de unidades', 'Proyección constante para los próximos 3 meses, sin estacionalidad. MAPE: prueba retrospectiva en los últimos 3 meses, usando solo datos anteriores.', [('Productos','Categoria'),('Productos','Marca')]))
    for i,(n,l) in enumerate([('Unidades vendidas','Unidades históricas'),('Proyeccion proximo mes','Proyección mensual (uds.)'),('Mes proyectado','Primer mes proyectado'),('MAPE prueba 3 meses','MAPE histórico (3 meses)')]): card(n,24+312*i,l)
    chart('Demanda real y estimación con los 3 meses anteriores','lineChart',col('Calendario','AñoMes'),['Unidades vendidas','Media movil 3 meses'],24,278,1232,228,False)
    table('Demanda y proyección por categoría',[col('Productos','Categoria'),measure('Unidades vendidas'),measure('Proyeccion proximo mes'),measure('MAPE prueba 3 meses')],24,518,608,214)
    chart('Proyección de demanda: próximos 3 meses','clusteredColumnChart',col('HorizontePronostico','Mes'),['Proyeccion proximo mes'],648,518,608,214,False)
    order.append(page(5,'Indicadores de gestión','Rotación estimada, disponibilidad, cumplimiento y error de pronóstico', 'Rotación no anualizada: costo de venta estimado / inventario medio de cortes del período. El costo estándar no incluye variaciones históricas.', [('Calendario','Año'),('Productos','Categoria')]))
    for i,(n,l) in enumerate([('Rotacion estimada',None),('Disponibilidad referencias','Referencias con stock disponible'),('Entregas a tiempo','Puntualidad de proveedores'),('MAPE prueba 3 meses','Error de pronóstico (MAPE)')]): card(n,24+312*i,l)
    table('Indicadores por categoría',[col('Productos','Categoria'),measure('Rotacion estimada'),measure('Cobertura dias'),measure('Disponibilidad referencias'),measure('MAPE prueba 3 meses')],24,278,840,268)
    text('NIVEL DE SERVICIO\nPendiente de datos de pedidos.\nSe necesitan cantidades solicitadas y atendidas.\nLa disponibilidad de stock se muestra por separado.',884,278,372,268,16,'#16324F','#E1F3F0')
    text('CÓMO INTERPRETAR\nRotación: mayor valor implica más movimiento del inventario durante el período.\nDisponibilidad: proporción de referencias con stock disponible mayor a cero, al corte.\nPuntualidad: recepciones en fecha o antes / órdenes recibidas. MAPE: menor error es mejor.',24,566,1232,166,14,'#16324F','#FFFFFF')
    FILES['Report/definition/pages/pages.json']={'$schema':schema+'pagesMetadata/1.1.0/schema.json','pageOrder':order,'activePageName':order[0]}
    from acomodar_movil import generate_mobile_files
    FILES.update(generate_mobile_files(FILES))
    return FILES

if __name__ == '__main__':
    (ROOT/'scripts/medidas.json').write_text(json.dumps(MEASURES,ensure_ascii=False,indent=2),encoding='utf-8')
    if len(__import__('sys').argv)>1 and __import__('sys').argv[1]=='pack':
        files=build()
        output=ROOT/'MPS Supply Chain - Informe.pbix'
        source=output if output.exists() else ROOT/'Gestion de pronosticos.pbix'
        temporary=ROOT/'MPS Supply Chain - Informe.tmp.pbix'
        with zipfile.ZipFile(source) as src, zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED) as dst:
            for item in src.infolist():
                if item.filename.startswith('Report/definition/pages/') or item.filename=='SecurityBindings': continue
                dst.writestr(item,src.read(item.filename))
            for name,obj in files.items(): dst.writestr(name,json.dumps(obj,ensure_ascii=False,separators=(',',':')))
        temporary.replace(output)
        print(f'{output.name}: {len(files)} definiciones, {len(MEASURES)} medidas')
