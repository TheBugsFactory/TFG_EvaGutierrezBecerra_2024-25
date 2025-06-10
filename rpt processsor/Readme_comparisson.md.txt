################################################################################
#                       README - Script de Análisis de Simulaciones de Impacto
################################################################################

Fecha de última actualización: 2025-05-07

--------------------------------------------------------------------------------
## 1. Objetivo del Script
--------------------------------------------------------------------------------

El objetivo principal de este script de Python es automatizar el procesamiento y la visualización de datos de simulaciones de impacto craneal. Específicamente, se enfoca en:
    - Identificar y catalogar simulaciones con y sin casco.
    - Leer datos de aceleración (componentes A1, A2, A3) y presión intracraneal (en puntos superior "Top" e inferior "Bottom") desde archivos de reporte (`.rpt`).
    - Calcular la magnitud de la aceleración resultante.
    - Generar gráficas individuales para cada simulación mostrando:
        * Presión Top y Bottom vs. Tiempo.
        * Aceleración y Presiones (Top/Bottom) vs. Tiempo.
    - Permitir al usuario seleccionar pares de simulaciones (una "sin casco" y una "con casco") para comparación.
    - Generar gráficas comparativas para los pares seleccionados:
        * Comparación de la magnitud de aceleración.
        * Comparación de presiones Top (Coup) y Bottom (Contrecoup) con ejes Y duales (MPa para "sin casco", kPa para "con casco") para una mejor visualización debido a las diferencias de magnitud.
    - Guardar todas las gráficas generadas en un directorio de resultados especificado.

--------------------------------------------------------------------------------
## 2. Funcionamiento del Script
--------------------------------------------------------------------------------

El script opera de la siguiente manera:

1.  **Configuración Inicial**: Lee las rutas de los directorios de entrada (donde se encuentran los reportes de simulación) y salida (donde se guardarán las gráficas). También define palabras clave para identificar simulaciones con y sin casco, y los nombres/sufijos esperados de los archivos `.rpt`.
2.  **Identificación de Simulaciones**:
    * Escanea el directorio raíz de reportes (`REPORTS_ROOT_DIR`) en busca de subdirectorios.
    * Clasifica cada subdirectorio como simulación "con casco" o "sin casco" basándose en la presencia de las `HELMET_KEYWORDS` o `NO_HELMET_KEYWORDS` (en minúsculas) en el nombre del subdirectorio.
3.  **Selección de Pares por el Usuario**:
    * Muestra al usuario listas numeradas de las simulaciones "sin casco" y "con casco" encontradas.
    * Solicita al usuario que introduzca los números correspondientes para formar pares de comparación.
4.  **Procesamiento de Datos por Par**: Para cada par seleccionado:
    * **Lectura de Datos**:
        * Localiza los archivos `.rpt` relevantes para las componentes de aceleración (A1, A2, A3) y las presiones (Top, Bottom) dentro de los directorios de cada simulación del par. Utiliza una función flexible (`find_rpt_file_flexible`) que intenta varias estrategias para encontrar los archivos.
        * Lee los datos de tiempo y valor de estos archivos. Las líneas de cabecera o no numéricas son ignoradas según los patrones definidos en `RPT_IGNORE_LINE_PATTERNS`.
        * El tiempo se convierte a **milisegundos (ms)**.
    * **Cálculo de Magnitud de Aceleración**:
        * Las componentes de aceleración (originalmente en mm/s²) se convierten a m/s².
        * Se calcula la magnitud resultante: $ \sqrt{A1^2 + A2^2 + A3^2} $ (en m/s²).
        * Se manejan posibles desajustes en las longitudes de los vectores de tiempo de las componentes truncando a la longitud mínima común.
    * **Preparación de Datos de Presión**:
        * Se asume que los datos de presión en los archivos `.rpt` están en **MegaPascales (MPa)**.
5.  **Generación de Gráficas**:
    * **Gráficas Individuales**: Para cada simulación (tanto "sin casco" como "con casco" del par procesado):
        1.  `Individual_{NombreSim}_Pressures_Only.png`: Presión Top (MPa) y Presión Bottom (MPa) vs. Tiempo (ms).
        2.  `Individual_{NombreSim}_Acc_And_Pressures.png`: Magnitud de Aceleración (m/s²) en un eje Y, y Presión Top (MPa) y Bottom (MPa) en un segundo eje Y, ambas vs. Tiempo (ms).
    * **Gráficas Comparativas**: Para el par de simulaciones:
        1.  `Compare_AccMag_{NombreNH}_vs_{NombreH}.png`: Comparación de la Magnitud de Aceleración (m/s²) vs. Tiempo (ms).
        2.  `Compare_Pressure_DualAxes_{NombreNH}_vs_{NombreH}.png`: Dos subplots:
            * **Presión Top (Coup)**: Eje Y izquierdo para "Sin Casco" (MPa), eje Y derecho para "Con Casco" (kPa), vs. Tiempo (ms).
            * **Presión Bottom (Contrecoup)**: Eje Y izquierdo para "Sin Casco" (MPa), eje Y derecho para "Con Casco" (kPa), vs. Tiempo (ms).
6.  **Guardado de Resultados**: Todas las gráficas se guardan en el directorio `RESULTS_COMPARISON_DIR`.

--------------------------------------------------------------------------------
## 3. Configuración del Script
--------------------------------------------------------------------------------

Antes de ejecutar el script, es crucial configurar las siguientes variables globales al inicio del archivo Python:

* `REPORTS_ROOT_DIR`: Ruta absoluta al directorio raíz que contiene las carpetas de cada simulación individual (ej., `/ruta/a/mis/simulaciones/Reports2`).
* `RESULTS_COMPARISON_DIR`: Ruta absoluta al directorio donde se guardarán todas las gráficas generadas (ej., `/ruta/a/mis/resultados/Results_Comparison`). El script creará este directorio si no existe.

* `NO_HELMET_KEYWORDS`: Lista de strings (en minúsculas) para identificar carpetas de simulaciones sin casco. Ej: `['nohelmet', 'sincasco', 'nahum']`.
* `HELMET_KEYWORDS`: Lista de strings (en minúsculas) para identificar carpetas de simulaciones con casco. Ej: `['helmet', 'concasco', 'base']`.

* `ACCEL_COMPONENTS_RPT_NAMES`: Un diccionario que mapea las claves 'A1', 'A2', 'A3' a los nombres exactos (o sufijos únicos) de los archivos `.rpt` de las componentes de aceleración.
    * Ejemplo: `{'A1': 'A1_Acc_mean.rpt', 'A2': 'A2_Acc_mean.rpt', 'A3': 'A3_Acc_mean.rpt'}`.
* `PRESSURE_TOP_RPT_SUFFIX`: El sufijo (o nombre completo si es consistente) del archivo `.rpt` para la presión en la parte superior.
    * Ejemplo: `"_Pressure_TOPREF_mean.rpt"`.
* `PRESSURE_BOTTOM_RPT_SUFFIX`: El sufijo (o nombre completo) del archivo `.rpt` para la presión en la parte inferior.
    * Ejemplo: `"_Pressure_BOTTOMREF_mean.rpt"`.

* `TIME_COLUMN_INDEX`: Índice de la columna de tiempo en los archivos `.rpt` (basado en 0). Por defecto es `0`.
* `VALUE_COLUMN_INDEX`: Índice de la columna de valor en los archivos `.rpt` (basado en 0). Por defecto es `1`.
* `RPT_IGNORE_LINE_PATTERNS`: Lista de patrones de expresiones regulares para identificar y omitir líneas de cabecera o no deseadas en los archivos `.rpt`.

--------------------------------------------------------------------------------
## 4. Arquitectura de Carpetas Esperada
--------------------------------------------------------------------------------

El script espera la siguiente estructura de directorios para los datos de entrada:

<REPORTS_ROOT_DIR>/
|
|--- <NombreSimulacion_SinCasco_1>/      <-- Debe contener una keyword de NO_HELMET_KEYWORDS
|    |--- A1_Acc_mean.rpt
|    |--- A2_Acc_mean.rpt
|    |--- A3_Acc_mean.rpt
|    |--- SimName_Pressure_TOPREF_mean.rpt  <-- O el nombre exacto/sufijo configurado
|    +--- SimName_Pressure_BOTTOMREF_mean.rpt <-- O el nombre exacto/sufijo configurado
|
|--- <NombreSimulacion_ConCasco_1>/      <-- Debe contener una keyword de HELMET_KEYWORDS
|    |--- A1_Acc_mean.rpt
|    |--- A2_Acc_mean.rpt
|    |--- A3_Acc_mean.rpt
|    |--- SimName_Pressure_TOPREF_mean.rpt
|    +--- SimName_Pressure_BOTTOMREF_mean.rpt
|
|--- <NombreSimulacion_SinCasco_2>/
|    |--- ... (archivos rpt)
|
+--- ... (más carpetas de simulación)


**Notas sobre nombres de archivo dentro de las carpetas de simulación:**
* Los nombres de los archivos de componentes de aceleración deben coincidir con los definidos en `ACCEL_COMPONENTS_RPT_NAMES`.
* Los nombres de los archivos de presión pueden ser:
    1.  `<NombreSimulacion><SUFFIX_PRESION>` (ej. `NombreSimulacion_SinCasco_1_Pressure_TOPREF_mean.rpt`)
    2.  El propio sufijo sin el nombre de la simulación si este es único dentro de la carpeta (ej. `Pressure_TOPREF_mean.rpt`). La función `find_rpt_file_flexible` intentará varias combinaciones.

Las gráficas generadas se guardarán en `RESULTS_COMPARISON_DIR`.

--------------------------------------------------------------------------------
## 5. Flujo de Trabajo del Usuario
--------------------------------------------------------------------------------

1.  **Preparar Datos**: Asegurarse de que todas las simulaciones estén en sus respectivas carpetas dentro de `REPORTS_ROOT_DIR` y que los archivos `.rpt` necesarios estén presentes y correctamente nombrados.
2.  **Configurar Script**: Abrir el script de Python y ajustar las variables en la sección "Configuración General" y "Configuración de Identificación de Simulaciones y Archivos" para que coincidan con la estructura de directorios y los nombres de archivo.
3.  **Ejecutar Script**: Correr el script desde un entorno Python que tenga las librerías necesarias instaladas (`numpy`, `matplotlib`, `seaborn`).
4.  **Interacción**:
    * El script listará las simulaciones encontradas, separadas por "CON CASCO" y "SIN CASCO".
    * Seguir las instrucciones en la consola para seleccionar los pares de simulaciones que se desean comparar introduciendo los números correspondientes.
    * Se puede introducir 'fin' para terminar la selección de pares.
5.  **Revisar Resultados**: Una vez que el script termine de procesar los pares seleccionados, navegar al directorio `RESULTS_COMPARISON_DIR` para encontrar todas las gráficas `.png` generadas.

--------------------------------------------------------------------------------
## 6. Consideraciones Adicionales
--------------------------------------------------------------------------------

* **Formato de Archivos `.rpt`**: El script asume que los archivos `.rpt` son archivos de texto donde los datos numéricos de tiempo y valor están en columnas separadas por espacios. Las líneas que no se ajustan a este formato o que coinciden con `RPT_IGNORE_LINE_PATTERNS` serán ignoradas.
* **Unidades**:
    * **Tiempo**: Se lee en segundos desde los `.rpt` y se convierte internamente a milisegundos (ms) para todas las operaciones y gráficas.
    * **Aceleración**: Se espera que los archivos `.rpt` de componentes de aceleración (A1, A2, A3) estén en **mm/s²**. El script los convierte a **m/s²** para el cálculo de la magnitud y para las gráficas.
    * **Presión**: Se espera que los archivos `.rpt` de presión (`_Pressure_TOPREF_mean.rpt`, `_Pressure_BOTTOMREF_mean.rpt`) estén en **MegaPascales (MPa)**. En las gráficas comparativas de presión, la simulación "Con Casco" se muestra en **kiloPascales (kPa)** para mejorar la visualización, mientras que "Sin Casco" permanece en MPa.
* **Consistencia de Datos**: Para el cálculo de la magnitud de aceleración, si los vectores de tiempo de las componentes A1, A2, A3 no son idénticos o no tienen la misma longitud, el script intentará truncarlos a la longitud mínima común y emitirá una advertencia. Para análisis más precisos con tiempos dispares, se requeriría una lógica de interpolación (no implementada actualmente).
* **Errores**: El script incluye manejo básico de errores, como archivos no encontrados o datos no numéricos. Los mensajes de error y advertencia se imprimen en la consola.
* **Dependencias**: Este script requiere las siguientes librerías de Python:
    * `os`
    * `re`
    * `numpy`
    * `matplotlib`
    * `seaborn`
    * `traceback`
    * `typing` (para anotaciones de tipo, generalmente parte de la librería estándar de Python 3.5+)
    Asegúrate de tenerlas instaladas en tu entorno Python (ej. `pip install numpy matplotlib seaborn`).
* **Personalización de Gráficas**: Los estilos de las gráficas (colores, tipos de línea) se definen utilizando `seaborn` y la paleta `COMPARISON_PALETTE`. Estos pueden ser modificados en el script si se desea un estilo visual diferente.
