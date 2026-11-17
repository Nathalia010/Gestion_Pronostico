# MPS | Supply Chain & Sales Analytics

Proyecto de portafolio de análisis de ventas, productos, inventario e importaciones de una empresa mayorista de tecnología. **Todos los datos son ficticios y no representan información real de MPS Colombia.**

Abre **MPS Supply Chain - Informe.pbix** en Power BI Desktop. El archivo contiene datos importados y cinco páginas interactivas:

1. **Resumen ejecutivo:** ventas, unidades, referencias activas, inventario y distribución de ventas.
2. **Productos e inventario:** stock disponible, cobertura, riesgo y detalle por referencia.
3. **Importaciones:** órdenes, costos, recepción, tiempos de entrega y puntualidad por proveedor.
4. **Pronósticos:** histórico mensual, media móvil, proyección de los próximos tres meses y error retrospectivo.
5. **Indicadores de gestión:** rotación estimada, disponibilidad, puntualidad y MAPE.

## Criterios de cálculo

- Período histórico: enero de 2025 a octubre de 2026. Moneda: COP.
- Las tablas de ventas, inventario e importaciones se relacionan con el calendario; importaciones utiliza la fecha de pedido.
- Las fechas originales están almacenadas como números de serie de Excel. Las relaciones utilizan esos valores, y las medidas convierten a fecha cuando realizan operaciones de calendario.
- El inventario corresponde al último corte disponible hasta el final del período seleccionado. No se suman existencias de distintos cortes.
- Stock disponible = stock total menos stock reservado.
- Cobertura = stock disponible / demanda diaria. La demanda diaria usa los últimos tres meses del histórico y una convención de 30 días por mes. Riesgo: cobertura inferior a 30 días.
- La proyección usa la media de unidades de los últimos tres meses del histórico. Cada mes futuro tiene el mismo valor; el modelo base no incorpora estacionalidad, tendencia ni intervalos de predicción.
- MAPE = promedio del error porcentual absoluto de los últimos tres meses históricos. Cada predicción utiliza exclusivamente los tres meses anteriores al mes evaluado. Los meses sin demanda real positiva se excluyen del promedio. Esta evaluación retrospectiva es de un paso, con origen móvil.
- La demanda reciente y el MAPE utilizan el cierre global del histórico; conservan los filtros de producto, pero no los filtros de calendario. No deben interpretarse como un pronóstico recalculado al cierre de cada selección de año.
- Rotación estimada = costo de ventas calculado con el costo estándar del producto / inventario medio de los cortes del período. No se anualiza.
- Puntualidad = órdenes recibidas hasta la fecha esperada / órdenes con fecha de recepción. No equivale al nivel de servicio a clientes.
- El nivel de servicio a clientes queda pendiente porque faltan las cantidades solicitadas y atendidas por pedido. La disponibilidad de referencias es una métrica distinta.

## Archivos

- `MPS Supply Chain - Informe.pbix`: informe final.
- `Gestion de pronosticos.pbix`: archivo de trabajo del proyecto.
- `respaldos/Gestion de pronosticos - original.pbix`: respaldo previo a los cambios.
- `scripts/medidas.json`: definiciones de las 30 medidas DAX.
- `scripts/crear_informe.py`: genera las medidas y empaqueta las cinco páginas PBIR sobre el modelo existente.
- `scripts/modelo_powerbi.ps1`: consulta el modelo local o aplica medidas y relaciones mediante la biblioteca oficial de Microsoft.

El modelo conserva sus conexiones originales. Para actualizar desde otra ubicación, ajusta el origen en **Transformar datos > Configuración de origen de datos** a la copia local del Excel de este repositorio.

La tabla calculada desconectada `HorizontePronostico` permite mostrar los tres meses futuros:

```dax
HorizontePronostico =
VAR Ultima = CONVERT(MAX(Ventas[FechaVenta]), DATETIME)
VAR Base = DATE(YEAR(Ultima), MONTH(Ultima), 1)
RETURN
    SELECTCOLUMNS(
        GENERATESERIES(1, 3),
        "Mes", FORMAT(EDATE(Base, [Value]), "yyyy-MM"),
        "Orden", [Value]
    )
```

La biblioteca de Microsoft usada para trabajar con el modelo y los archivos temporales están excluidos de Git en `.tools/`.
