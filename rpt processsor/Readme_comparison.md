## 1. Objetivo del Script

El objetivo principal de este script de Python es automatizar el procesamiento y la visualización de datos de simulaciones de impacto craneal. Específicamente, se enfoca en:

-   Identificar y catalogar simulaciones con y sin casco.
-   Leer datos de aceleración (componentes A1, A2, A3) y presión intracraneal (en puntos superior "Top" e inferior "Bottom") desde archivos de reporte (`.rpt`).
-   Calcular la magnitud de la aceleración resultante.
-   Generar gráficas individuales para cada simulación mostrando:
    -   Presión Top y Bottom vs. Tiempo.
    -   Aceleración y Presiones (Top/Bottom) vs. Tiempo.
-   Permitir al usuario seleccionar pares de simulaciones (una "sin casco" y una "con casco") para comparación.
-   Generar gráficas comparativas para los pares seleccionados:
    -   Comparación de la magnitud de aceleración.
    -   Comparación de presiones Top (Coup) y Bottom (Contrecoup) con ejes Y duales (MPa para "sin casco", kPa para "con casco") para una mejor visualización debido a las diferencias de magnitud.
-   Guardar todas las gráficas generadas en un directorio de resultados especificado.

---

## 2. Funcionamiento del Script

El script opera de la siguiente manera:

1.  **Configuración Inicial**: Lee las rutas de los directorios de entrada (donde se encuentran los reportes de simulación) y salida (donde se guardarán las gráficas). También define palabras clave para identificar simulaciones con y sin casco, y los nombres/sufijos esperados de los archivos `.rpt`.
2.  **Identificación de Simulaciones**:
    -   Escanea el directorio raíz de reportes (`REPORTS_ROOT_DIR`) en busca de subdirectorios.
    -   Clasifica cada subdirectorio como simulación "con casco" o "sin casco" basándose en la presencia de las `HELMET_KEYWORDS` o `NO_HELMET_KEYWORDS` (en minúsculas) en el nombre del subdirectorio.
3.  **Selección de Pares por el Usuario**:
    -   Muestra al usuario listas numeradas de las simulaciones "sin casco" y "con casco" encontradas.
    -   Solicita al usuario que introduzca los números correspondientes para formar pares de comparación.
4.  **Procesamiento de Datos por Par**: Para cada par seleccionado:
    -   **Lectura de Datos**:
        -   Localiza los archivos `.rpt` relevantes para las componentes de aceleración (A1, A2, A3) y las presiones (Top, Bottom) dentro de los directorios de cada simulación del par. Utiliza una función flexible (`find_rpt_file_flexible`) que intenta varias estrategias para encontrar los archivos.
        -   Lee los datos de tiempo y valor de estos archivos. Las líneas de cabecera o no numéricas son ignoradas según los patrones definidos en `RPT_IGNORE_LINE_PATTERNS`.
        -   El tiempo se convierte a **milisegundos (ms)**.
    -   **Cálculo de Magnitud de Aceleración**:
        -   Las componentes de aceleración (originalmente en mm/s²) se convierten a m/s².
        -   Se calcula la magnitud resultante: $ \sqrt{A1^2 + A2^2 + A3^2} $ (en m/s²).
        -   Se manejan posibles desajustes en las longitudes de los vectores de tiempo de las componentes truncando a la longitud mínima común.
    -   **Preparación de Datos de Presión**:
        -   Se asume que los datos de presión en los archivos `.rpt` están en **MegaPascales (MPa)**.
5.  **Generación de Gráficas**:
    -   **Gráficas Individuales**: Para cada simulación (tanto "sin casco" como "con casco" del par procesado):
        1.  `Individual_{NombreSim}_Pressures_Only.png`: Presión Top (MPa) y Presión Bottom (MPa) vs. Tiempo (ms).
        2.  `Individual_{NombreSim}_Acc_And_Pressures.png`: Magnitud de Aceleración (m/s²) en un eje Y, y Presión Top (MPa) y Bottom (MPa) en un segundo eje Y, ambas vs. Tiempo (ms).
    -   **Gráficas Comparativas**: Para el par de simulaciones:
        1.  `Compare_AccMag_{NombreNH}_vs_{NombreH}.png`: Comparación de la Magnitud de Aceleración (m/s²) vs. Tiempo (ms).
        2.  `Compare_Pressure_DualAxes_{NombreNH}_vs_{NombreH}.png`: Dos subplots:
            -   **Presión Top (Coup)**: Eje Y izquierdo para "Sin Casco" (MPa), eje Y derecho para "Con Casco" (kPa), vs. Tiempo (ms).
            -   **Presión Bottom (Contrecoup)**: Eje Y izquierdo para "Sin Casco" (MPa), eje Y derecho para "Con Casco" (kPa), vs. Tiempo (ms).
6.  **Guardado de Resultados**: Todas las gráficas se guardan en el directorio `RESULTS_COMPARISON_DIR`.

---

## 3. Configuración del Script

Antes de ejecutar el script, es crucial configurar las siguientes variables globales al inicio del archivo Python:

*   `REPORTS_ROOT_DIR`: Ruta absoluta al directorio raíz que contiene las carpetas de cada simulación.
    -   Ejemplo: `'/ruta/a/mis/simulaciones/Reports2'`
*   `RESULTS_COMPARISON_DIR`: Ruta absoluta al directorio donde se guardarán todas las gráficas generadas. El script creará este directorio si no existe.
    -   Ejemplo: `'/ruta/a/mis/resultados/Results_Comparison'`
*   `NO_HELMET_KEYWORDS`: Lista de strings (en minúsculas) para identificar carpetas sin casco.
    -   Ejemplo: `['nohelmet', 'sincasco', 'nahum']`
*   `HELMET_KEYWORDS`: Lista de strings (en minúsculas) para identificar carpetas con casco.
    -   Ejemplo: `['helmet', 'concasco', 'base']`
*   `ACCEL_COMPONENTS_RPT_NAMES`: Diccionario que mapea claves a los nombres de los archivos `.rpt` de aceleración.
    -   Ejemplo: `{'A1': 'A1_Acc_mean.rpt', 'A2': 'A2_Acc_mean.rpt', 'A3': 'A3_Acc_mean.rpt'}`
*   `PRESSURE_TOP_RPT_SUFFIX`: Sufijo del archivo `.rpt` para la presión superior.
    -   Ejemplo: `"_Pressure_TOPREF_mean.rpt"`
*   `PRESSURE_BOTTOM_RPT_SUFFIX`: Sufijo del archivo `.rpt` para la presión inferior.
    -   Ejemplo: `"_Pressure_BOTTOMREF_mean.rpt"`
*   `TIME_COLUMN_INDEX`: Índice de la columna de tiempo en los `.rpt` (por defecto `0`).
*   `VALUE_COLUMN_INDEX`: Índice de la columna de valor en los `.rpt` (por defecto `1`).
*   `RPT_IGNORE_LINE_PATTERNS`: Lista de expresiones regulares para omitir líneas de cabecera.

---

## 4. Arquitectura de Carpetas Esperada

El script espera la siguiente estructura de directorios para los datos de entrada:

```plaintext
<REPORTS_ROOT_DIR>/
|
|--- <NombreSimulacion_SinCasco_1>/      <-- Debe contener una keyword de NO_HELMET_KEYWORDS
|    |--- A1_Acc_mean.rpt
|    |--- A2_Acc_mean.rpt
|    |--- A3_Acc_mean.rpt
|    |--- SimName_Pressure_TOPREF_mean.rpt  <-- O el nombre/sufijo configurado
|    +--- SimName_Pressure_BOTTOMREF_mean.rpt <-- O el nombre/sufijo configurado
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
```

**Notas sobre nombres de archivo:**
*   Los nombres de los archivos de componentes de aceleración deben coincidir con los definidos en `ACCEL_COMPONENTS_RPT_NAMES`.
*   Los nombres de los archivos de presión pueden ser:
    1.  `<NombreSimulacion><SUFFIX_PRESION>` (ej. `Sim_SinCasco_1_Pressure_TOPREF_mean.rpt`)
    2.  El propio sufijo si es único dentro de la carpeta (ej. `Pressure_TOPREF_mean.rpt`). La función `find_rpt_file_flexible` intentará varias combinaciones.

Las gráficas generadas se guardarán en `RESULTS_COMPARISON_DIR`.

---

## 5. Flujo de Trabajo del Usuario

1.  **Preparar Datos**: Asegurarse de que todas las simulaciones estén en sus carpetas dentro de `REPORTS_ROOT_DIR` y que los archivos `.rpt` necesarios estén presentes.
2.  **Configurar Script**: Abrir el script de Python y ajustar las variables de configuración para que coincidan con la estructura y nombres de archivo.
3.  **Ejecutar Script**: Correr el script desde un entorno Python con las librerías necesarias.
4.  **Interacción**:
    -   El script listará las simulaciones encontradas, separadas por "CON CASCO" y "SIN CASCO".
    -   Seguir las instrucciones en la consola para seleccionar los pares a comparar introduciendo sus números.
    -   Introducir `'fin'` para terminar la selección.
5.  **Revisar Resultados**: Navegar al directorio `RESULTS_COMPARISON_DIR` para encontrar todas las gráficas `.png` generadas.

---

## 6. Consideraciones Adicionales

*   **Formato de `.rpt`**: Se asume que son archivos de texto con columnas de tiempo y valor separadas por espacios. Las líneas que no coincidan o que estén en `RPT_IGNORE_LINE_PATTERNS` serán ignoradas.
*   **Unidades**:
    -   **Tiempo**: Se lee en segundos y se convierte internamente a **milisegundos (ms)**.
    -   **Aceleración**: Se espera en **mm/s²** en los `.rpt` y se convierte a **m/s²**.
    -   **Presión**: Se espera en **MegaPascales (MPa)**. En las gráficas comparativas, "Con Casco" se muestra en **kiloPascales (kPa)** para mejor visualización.
*   **Consistencia de Datos**: Si los vectores de tiempo para A1, A2, A3 difieren en longitud, se truncan a la longitud mínima común y se emite una advertencia. Una lógica de interpolación no está implementada.
*   **Errores**: El script incluye manejo básico de errores. Los mensajes de error y advertencia se imprimen en la consola.
*   **Dependencias**: Este script requiere las siguientes librerías de Python:
    -   `os`
    -   `re`
    -   `numpy`
    -   `matplotlib`
    -   `seaborn`
    -   `traceback`
    -   `typing` (estándar en Python 3.5+)

    Asegúrate de tenerlas instaladas: `pip install numpy matplotlib seaborn`.
*   **Personalización de Gráficas**: Los estilos se definen con `seaborn` y se pueden modificar directamente en el script.
