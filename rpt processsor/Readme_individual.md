## Introducción

Este documento describe cómo ejecutar el script de Python v1.6+ (que utiliza la librería Seaborn para generar gráficos mejorados y que incluye correcciones para el almacenamiento de resultados HIC) en el entorno de Google Colaboratory (Colab).

El script procesa archivos `.rpt` de Abaqus ubicados en una estructura de carpetas específica (`Reports`) y genera varios gráficos `.png` en una carpeta `Results`, incluyendo:
*   Gráficos individuales por simulación:
    *   Presión vs Tiempo (si existen archivos `Pressure_*.rpt`).
    *   Magnitud de Aceleración vs Tiempo (en m/s²).
    *   Magnitud de Aceleración vs Tiempo (en g).
*   Gráficos agregados (resumen de todas las simulaciones):
    *   HIC vs Velocidad de Impacto (un gráfico por cada duración HIC calculada, p.ej., 5ms, 10ms, 15ms).
    *   PLA (eje izq.) y Máximo HIC (eje der.) vs Velocidad de Impacto (gráfico con ejes gemelos).

Google Colab proporciona un entorno de ejecución gratuito, pero requiere pasos específicos para cargar datos y guardar resultados debido a su gestión de archivos temporal.

---

## Requisitos Previos

1.  **Script de Python:** El archivo `.py` de la versión **MÁS RECIENTE** del script (v1.6 o posterior, con las correcciones de `hic_results`), o el código listo para copiar/pegar.
2.  **Carpeta `Reports`:** Tu carpeta local que contiene:
    *   Subcarpetas para cada simulación (p.ej., `Sim1_v1000`, `Sim2_v2000`). **Importante:** Para que se extraiga la velocidad, el nombre debe incluir `_vNUMERO` (p.ej., `_v3400`).
    *   Dentro de cada subcarpeta, los archivos `.rpt` necesarios, **críticamente** `A1_Acc_mean.rpt`, `A2_Acc_mean.rpt` y `A3_Acc_mean.rpt`. Sin estos 3, los cálculos de Aceleración, PLA y HIC fallarán para esa simulación.
3.  **Archivo `Reports.zip`:** Una versión comprimida (en formato ZIP) de tu carpeta `Reports`.

---

## Método 1: Usando Carga de Archivo ZIP (Recomendado para Empezar)

Rápido y sencillo, pero los archivos se borran al finalizar la sesión de Colab.

**Paso 1: Abrir Colab y Subir `Reports.zip`**
-   Ve a [Google Colab](https://colab.research.google.com/) y crea un nuevo cuaderno.
-   Panel izquierdo > icono Carpeta > botón "Subir" > selecciona `Reports.zip`. Espera a que finalice la subida.

**Paso 2: Descomprimir `Reports.zip`**
-   Crea una nueva celda de código (`+ Código`).
-   Pega y ejecuta (Shift + Enter):
    ```bash
    !unzip Reports.zip
    ```
-   Verifica que la carpeta `Reports` aparezca en el panel de archivos de la izquierda.

**Paso 3: Instalar Librerías (Si es necesario)**
-   Crea una nueva celda de código. Pega y ejecuta:
    ```bash
    !pip install seaborn matplotlib numpy pandas
    ```

**Paso 4: Pegar y Ejecutar el Script Python**
-   Crea una nueva celda de código.
-   Pega *todo* el contenido de tu script de Python (la versión corregida v1.6+).
-   Ejecuta la celda (Shift + Enter).
-   Observa la salida. Si no detecta la velocidad (`_vNUMERO`), te la pedirá; introduce el valor numérico y pulsa Enter.

**Paso 5: Acceder y Descargar Resultados**
-   La carpeta `Results` aparecerá en el panel de archivos.
-   Explora `Results` y sus subcarpetas para ver los archivos `.png`.
-   Para descargar un solo archivo: Clic derecho sobre el archivo > Descargar.
-   Para descargar toda la carpeta `Results` como un archivo ZIP:
    -   Crea una nueva celda de código. Pega y ejecuta:
        ```bash
        !zip -r /content/Results_Output.zip /content/Results
        ```
    -   Espera a que se cree el archivo `Results_Output.zip` en el panel de archivos.
    -   Clic derecho sobre `Results_Output.zip` > Descargar.

---

## Método 2: Usando Google Drive (Para Persistencia)

Los datos y resultados permanecen en tu Drive entre sesiones.

**Paso 1: Subir Carpeta `Reports` a Google Drive**
-   Sube tu carpeta `Reports` (la original, no el ZIP) a tu Google Drive.

**Paso 2: Montar Google Drive en Colab**
-   Crea una nueva celda de código. Pega y ejecuta:
    ```python
    from google.colab import drive
    drive.mount('/content/drive')
    ```
-   Sigue las instrucciones en la salida para autorizar el acceso a tu cuenta de Google. Tu Drive estará disponible en la ruta `/content/drive/MyDrive/`.

**Paso 3: Modificar Rutas en el Script Python**
-   **ANTES** de ejecutar el script, edita las siguientes variables en el código:
    ```python
    # AJUSTA ESTAS RUTAS:
    REPORTS_ROOT_DIR = '/content/drive/MyDrive/Reports' # Ruta a tu carpeta Reports en Drive
    RESULTS_DIR = '/content/drive/MyDrive/MisResultadosSimulacion' # Donde guardar resultados en Drive
    ```

**Paso 4: Instalar Librerías (Si es necesario)**
-   Igual que en el Método 1, Paso 3 (`!pip install ...`).

**Paso 5: Pegar y Ejecutar el Script Modificado**
-   Crea una nueva celda de código. Pega el script (ya con las rutas modificadas). Ejecuta la celda.

**Paso 6: Acceder a los Resultados en Google Drive**
-   Los resultados aparecerán directamente en la carpeta que indicaste en `RESULTS_DIR` dentro de tu Google Drive.

---

## Arquitectura de Carpetas (Colab vs. Script)

*   `/content/`: Es el directorio raíz temporal del entorno de ejecución de Colab.
*   **Script y Rutas Relativas:** Por defecto, el script usa `REPORTS_ROOT_DIR = 'Reports'` y `RESULTS_DIR = 'Results'`, lo que significa que espera encontrar/crear estas carpetas directamente en `/content/`. Esto funciona perfectamente con el **Método 1**.
*   **Google Drive y Rutas Absolutas:** Al montar Drive (**Método 2**), tus archivos están en `/content/drive/MyDrive/...`. Por eso es crucial usar estas rutas absolutas en las variables `REPORTS_ROOT_DIR` y `RESULTS_DIR` del script.
*   **Naturaleza Temporal:** Recuerda que todo lo que esté en `/content/` (excepto el contenido montado de Drive) se borrará al finalizar la sesión. Usa Drive o descarga tus resultados.

---

## Comandos Importantes (Resumen)

*   `!unzip <archivo.zip>`: Descomprime un archivo ZIP.
*   `!pip install <librerias>`: Instala librerías de Python.
*   `from google.colab import drive; drive.mount('/content/drive')`: Conecta y monta tu Google Drive.
*   `!zip -r <salida.zip> <origen>`: Comprime una carpeta para facilitar su descarga.

---

## Solución de Problemas Comunes (Troubleshooting)

*   **Warnings: "Cannot generate aggregate plot" / "No sims with HIC & Velocity found"**
    *   **Significado:** El script terminó de procesar las simulaciones individuales, pero no pudo recopilar suficientes datos combinados (Velocidad, PLA, HIC) para generar los gráficos de resumen. Los gráficos individuales sí pueden haberse creado.
    *   **Causa Común (Histórica):** Versiones del script anteriores a ~v1.6 tenían un error que impedía guardar los valores HIC en el diccionario `hic_results`. **Asegúrate de usar la versión del script con la inicialización de `hic_results[sim_name]` corregida** (movida a *después* de validar los datos de aceleración).
    *   **Otras Causas:**
        *   **Faltan Archivos:** No existen los archivos `A1_Acc_mean.rpt`, `A2_Acc_mean.rpt`, y `A3_Acc_mean.rpt` dentro de las carpetas de simulación en `Reports`.
        *   **Archivos Corruptos:** Los archivos `.rpt` de aceleración están vacíos o tienen un formato que el script no puede leer.
        *   **Fallo en Cálculo:** Errores durante `calculate_acceleration_magnitude` (p.ej., los vectores de tiempo no coinciden).
        *   **Fallo en Velocidad:** Ninguna simulación tiene un nombre de carpeta con `_vNUMERO` y no se proporcionó una velocidad manual válida.
        *   **Fallo en HIC/PLA:** Errores inesperados en `calculate_hic` o al calcular el máximo (`np.max`) para el PLA.
*   **Cómo Diagnosticar:**
    *   **Revisa TODA la Salida:** No mires solo el final. Busca mensajes `ERROR:` o `WARNING:` que ocurran *antes* de los warnings finales. Estos indican el punto exacto del fallo (p.ej., "Failed to read", "Time vectors mismatch", "Cannot calculate magnitude").
    *   **Verifica Estructura y Nombres:** Confirma que la ruta `Reports/NombreSimulacion_vXXX/A*_Acc_mean.rpt` existe y que los nombres de las carpetas son correctos para extraer la velocidad.
    *   **Verifica Archivos RPT:** Abre manualmente algunos `.rpt` de aceleración para asegurarte de que contienen datos numéricos con el formato esperado.

---

## Consideraciones Adicionales

*   **Entrada Manual de Velocidad:** Si el script la pide, introduce solo el número y pulsa Enter. Dejarlo en blanco hará que esa simulación se omita de los gráficos agregados.
*   **Manejo de Errores:** `ERROR:` indica un fallo que detiene una parte del proceso; `WARNING:` indica un posible problema o dato faltante que puede o no ser crítico. `traceback` proporciona detalles técnicos del error para depuración.
*   **Limitaciones de Recursos:** La versión gratuita de Colab tiene límites de tiempo de ejecución y recursos. Para trabajos muy grandes o largos, considera dividir el trabajo en lotes o usar Colab Pro.
*   **Actualización de Librerías:** Puedes usar `!pip install --upgrade seaborn` para asegurarte de tener la última versión de una librería si es necesario.
