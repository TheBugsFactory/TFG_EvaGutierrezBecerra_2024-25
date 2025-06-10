## Propósito

Este script de Python (compatible con Abaqus 6.12 y Python 2.x) automatiza la extracción de datos de resultados (Presión y Aceleración) desde múltiples archivos `.odb` de Abaqus. Genera archivos de reporte (`.rpt`) individuales y promediados para las variables y regiones especificadas.

**Importante:** Esta es la versión original del script. La configuración se realiza directamente modificando las variables dentro del código fuente del script.

---

## Archivos Necesarios

1.  `rpt_manager_v1.py` (o el nombre que le hayas dado al script original): El script principal de Python.
2.  Archivos `.odb`: Los archivos de resultados de Abaqus de los cuales se extraerán los datos. Deben estar en el mismo directorio que el script, o el script debe ejecutarse desde el directorio que los contiene.

---

## Cómo Usarlo

1.  **Preparación:**
    *   Asegúrate de tener Abaqus CAE instalado y que el entorno de Python de Abaqus esté configurado. Este script se ejecuta desde Abaqus CAE.
    *   Coloca el script `rpt_manager_v1.py` en el directorio que contiene tus archivos `.odb`.

2.  **Configuración (DENTRO DEL SCRIPT):**
    *   Abre el archivo `.py` (ej. `rpt_manager_v1.py`) con un editor de texto o un IDE de Python.
    *   Localiza la sección `--- Configuracion (AJUSTAR SEGUN SEA NECESARIO) ---` cerca del inicio de la función `process_odb_files()`.
    *   Modifica los valores de las siguientes variables directamente en el código:
        *   `NODE_SET_ACC`
        *   `ELEMENT_SETS_PRESSURE`
        *   `STEP_NAME`
        *   `INSTANCE_NAME`
        *   `REPORT_DIR_NAME`
        *   `PRESSURE_VAR`
        *   `ACCEL_VAR_PREFIX`
    *   Guarda los cambios en el archivo `.py`.

3.  **Ejecución:**
    *   Abre Abaqus CAE.
    *   Ve a `File > Run Script...`.
    *   Navega hasta el directorio donde guardaste el script `.py` modificado y selecciónalo.
    *   Haz clic en `OK`.
    *   El script comenzará a procesar los archivos `.odb`. Los mensajes de progreso se mostrarán en la ventana de mensajes de Abaqus.

4.  **Resultados:**
    *   Los archivos de reporte `.rpt` se crearán dentro de una subcarpeta (nombrada según `REPORT_DIR_NAME` en el script), y dentro de esta, en subcarpetas con el nombre de cada `.odb` procesado.

---

## Consideraciones Importantes

*   **Modificación Directa del Código:** Cualquier cambio en la configuración requiere editar y guardar el archivo `.py` directamente.
*   **Versión de Abaqus/Python:** Diseñado para Abaqus v6.12 (Python 2.x).
*   **Nombres Exactos:** Los nombres de `Step`, `Instance`, `ElementSets` y `NodeSets` definidos en el script deben coincidir **EXACTAMENTE** con los de tus archivos `.odb`.
*   **Ubicación de Sets:** El script busca Sets a nivel de `Assembly` y luego dentro de la `Instance` especificada.
*   **Limpieza de XYData:** El script limpia los `XYData` y `XYPlot` existentes en la sesión de Abaqus CAE antes de comenzar.

---

## Sección de Configuración Típica en el Script Original

```python
# --- Configuracion (AJUSTAR SEGUN SEA NECESARIO) ---
NODE_SET_ACC = 'SET-ACC-NODAL' # NodeSet para aceleracion
ELEMENT_SETS_PRESSURE = [      # ElementSets para presion
    'BACKREF', 'BOTTOMREF', 'CENTREOFMASSREF',
    'FRONTREF', 'LEFTREF', 'RIGHTREF', 'TOPREF'
]
# !IMPORTANTE!: Verifica que estos nombres coincidan EXACTAMENTE con tu ODB
STEP_NAME = 'Step-1'          # Nombre del Step de interes
INSTANCE_NAME = 'PART-1-1'    # Nombre de la instancia principal
REPORT_DIR_NAME = 'Reports'   # Nombre de la carpeta principal de reportes

# Variables de Output
PRESSURE_VAR = (('S', INTEGRATION_POINT, ((INVARIANT, 'Pressure'), )), )
ACCEL_VAR_PREFIX = 'Spatial acceleration'
```
