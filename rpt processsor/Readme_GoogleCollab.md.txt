################################################################################
# README: Ejecución del Script de Post-Procesamiento v1.6+ (Seaborn) en Google Colab #
################################################################################

-------------------------------------------------------------------------------
## Introducción ##
-------------------------------------------------------------------------------

Este documento describe cómo ejecutar el script de Python v1.6+ (que utiliza la librería Seaborn para generar gráficos mejorados y que incluye correcciones para el almacenamiento de resultados HIC) en el entorno de Google Colaboratory (Colab).

El script procesa archivos `.rpt` de Abaqus ubicados en una estructura de carpetas específica (`Reports`) y genera varios gráficos `.png` en una carpeta `Results`, incluyendo:
* Gráficos individuales por simulación:
    * Presión vs Tiempo (si existen archivos `Pressure_*.rpt`).
    * Magnitud de Aceleración vs Tiempo (en m/s²).
    * Magnitud de Aceleración vs Tiempo (en g).
* Gráficos agregados (resumen de todas las simulaciones):
    * HIC vs Velocidad de Impacto (un gráfico por cada duración HIC calculada, p.ej., 5ms, 10ms, 15ms).
    * PLA (eje izq.) y Máximo HIC (eje der.) vs Velocidad de Impacto (gráfico con ejes gemelos).

Google Colab proporciona un entorno de ejecución gratuito, pero requiere pasos específicos para cargar datos y guardar resultados debido a su gestión de archivos temporal.

-------------------------------------------------------------------------------
## Requisitos Previos ##
-------------------------------------------------------------------------------

1.  **Script de Python:** El archivo `.py` de la versión MÁS RECIENTE del script (v1.6 o posterior, con las correcciones de `hic_results`), o el código listo para copiar/pegar.
2.  **Carpeta `Reports`:** Tu carpeta local que contiene:
    * Subcarpetas para cada simulación (p.ej., `Sim1_v1000`, `Sim2_v2000`). **Importante:** Para que se extraiga la velocidad, el nombre debe incluir `_vNUMERO` (p.ej., `_v3400`).
    * Dentro de cada subcarpeta, los archivos `.rpt` necesarios, **críticamente** `A1_Acc_mean.rpt`, `A2_Acc_mean.rpt` y `A3_Acc_mean.rpt`. Sin estos 3, los cálculos de Aceleración, PLA y HIC fallarán para esa simulación.
3.  **Archivo `Reports.zip`:** Una versión comprimida (en formato ZIP) de tu carpeta `Reports`.

-------------------------------------------------------------------------------
## Método 1: Usando Carga de Archivo ZIP (Recomendado para Empezar) ##
-------------------------------------------------------------------------------

Rápido y sencillo, pero los archivos se borran al finalizar la sesión de Colab.

**Paso 1: Abrir Colab y Subir `Reports.zip`**
    - Ve a Google Colab (<https://colab.research.google.com/>) y crea un nuevo cuaderno.
    - Panel izquierdo > icono Carpeta > botón "Subir" > selecciona `Reports.zip`. Espera.

**Paso 2: Descomprimir `Reports.zip`**
    - Nueva celda de código (+ Código).
    - Pega y ejecuta (Shift + Enter):
      ```bash
      !unzip Reports.zip
      ```
    - Verifica que la carpeta `Reports` aparezca en el panel de archivos.

**Paso 3: Instalar Librerías (Si es necesario)**
    - Nueva celda de código. Pega y ejecuta:
      ```bash
      !pip install seaborn matplotlib numpy pandas
      ```

**Paso 4: Pegar y Ejecutar el Script Python**
    - Nueva celda de código.
    - Pega *todo* el contenido de tu script de Python (la versión corregida v1.6+).
    - Ejecuta la celda (Shift + Enter).
    - Observa la salida. Si no detecta la velocidad (`_vNUMERO`), te la pedirá; introduce el valor numérico y pulsa Enter.

**Paso 5: Acceder y Descargar Resultados**
    - La carpeta `Results` aparecerá en el panel de archivos.
    - Explora `Results` y sus subcarpetas para ver los `.png`.
    - Descargar archivo: Clic derecho > Descargar.
    - Descargar todo `Results` como ZIP:
      - Nueva celda de código. Pega y ejecuta:
        ```bash
        !zip -r /content/Results_Output.zip /content/Results
        ```
      - Espera a que se cree `Results_Output.zip`.
      - Clic derecho sobre `Results_Output.zip` > Descargar.

-------------------------------------------------------------------------------
## Método 2: Usando Google Drive (Para Persistencia) ##
-------------------------------------------------------------------------------

Los datos y resultados permanecen en tu Drive.

**Paso 1: Subir Carpeta `Reports` a Google Drive**
    - Sube tu carpeta `Reports` (la original) a tu Google Drive.

**Paso 2: Montar Google Drive en Colab**
    - Nueva celda de código. Pega y ejecuta:
      ```python
      from google.colab import drive
      drive.mount('/content/drive')
      ```
    - Autoriza el acceso siguiendo las instrucciones. Tu Drive estará en `/content/drive/MyDrive/`.

**Paso 3: Modificar Rutas en el Script Python**
    - **ANTES** de ejecutar, edita estas variables en tu script:
      ```python
      # AJUSTA ESTAS RUTAS:
      REPORTS_ROOT_DIR = '/content/drive/MyDrive/Reports' # Ruta a tu carpeta Reports en Drive
      RESULTS_DIR = '/content/drive/MyDrive/MisResultadosSimulacion' # Donde guardar resultados en Drive
      ```

**Paso 4: Instalar Librerías (Si es necesario)**
    - Igual que en Método 1, Paso 3 (`!pip install ...`).

**Paso 5: Pegar y Ejecutar el Script Modificado**
    - Nueva celda de código. Pega el script (con rutas modificadas). Ejecuta.

**Paso 6: Acceder a los Resultados en Google Drive**
    - Los resultados aparecerán en la carpeta que indicaste en `RESULTS_DIR` en tu Drive.

-------------------------------------------------------------------------------
## Arquitectura de Carpetas (Colab vs. Script) ##
-------------------------------------------------------------------------------

* **`/content/`:** Directorio raíz temporal de Colab.
* **Script y Rutas Relativas:** El script usa `REPORTS_ROOT_DIR = 'Reports'` y `RESULTS_DIR = 'Results'`, esperando encontrarlas/crearlas directamente en `/content/` (funciona con Método 1).
* **Google Drive y Rutas Absolutas:** Al montar Drive (Método 2), tus archivos están en `/content/drive/MyDrive/...`. Debes usar estas rutas absolutas en las variables `REPORTS_ROOT_DIR` y `RESULTS_DIR` del script.
* **Naturaleza Temporal:** Recuerda que `/content/` se borra. Usa Drive o descarga los resultados.

-------------------------------------------------------------------------------
## Comandos Importantes (Resumen) ##
-------------------------------------------------------------------------------

* `!unzip <archivo.zip>`: Descomprime.
* `!pip install <librerias>`: Instala librerías.
* `from google.colab import drive; drive.mount('/content/drive')`: Conecta Google Drive.
* `!zip -r <salida.zip> <origen>`: Comprime una carpeta para descargarla.

-------------------------------------------------------------------------------
## Solución de Problemas Comunes (Troubleshooting) ##
-------------------------------------------------------------------------------

* **Warnings "Cannot generate aggregate plot" / "No sims with HIC & Velocity found":**
    * **Significado:** El script terminó de procesar simulaciones individuales, pero no pudo recopilar suficientes datos combinados (Velocidad, PLA, HIC) para generar los gráficos resumen. Los gráficos individuales sí pueden haberse creado.
    * **Causa Común (Histórica):** En versiones anteriores a la corrección (~v1.6+), había un error que impedía guardar los valores HIC calculados en el diccionario `hic_results`, aunque se calcularan bien. Asegúrate de usar la versión del script con la inicialización de `hic_results[sim_name]` corregida (movida a *después* de validar los datos de aceleración).
    * **Otras Causas:**
        * **Faltan Archivos:** No existen los archivos `A1_Acc_mean.rpt`, `A2_Acc_mean.rpt`, `A3_Acc_mean.rpt` dentro de las carpetas de simulación en `Reports`.
        * **Archivos Corruptos:** Los archivos `.rpt` de aceleración están vacíos o tienen un formato que el script no puede leer.
        * **Fallo en Cálculo de Aceleración:** Errores durante `calculate_acceleration_magnitude` (p.ej., vectores de tiempo no coinciden).
        * **Fallo en Extracción/Entrada de Velocidad:** Ninguna simulación tiene un nombre con `_vNUMERO` y no se proporcionó una velocidad manual válida para ninguna.
        * **Fallo en Cálculo HIC/PLA:** Errores no esperados en `calculate_hic` o al hacer `np.max` para PLA.
* **Cómo Diagnosticar:**
    * **Revisa TODA la Salida:** No mires solo el final. Busca mensajes `ERROR:` o `WARNING:` que ocurran *antes* de los warnings de los gráficos agregados. Estos indican el punto exacto del fallo (p.ej., "Failed read", "Time vectors mismatch", "Cannot calculate magnitude").
    * **Verifica Estructura y Nombres:** Confirma que `Reports/NombreSimulacion_vXXX/A*_Acc_mean.rpt` existe y que los nombres de carpeta son correctos para la velocidad.
    * **Verifica Archivos RPT:** Abre algunos `.rpt` de aceleración para asegurarte de que contienen datos numéricos esperados.

-------------------------------------------------------------------------------
## Consideraciones Adicionales ##
-------------------------------------------------------------------------------

* **Entrada Manual de Velocidad:** Si el script la pide, introduce un número y pulsa Enter. Dejarlo en blanco omite esa simulación para los gráficos agregados.
* **Manejo de Errores:** `ERROR:` indica un fallo; `WARNING:` indica un posible problema o dato faltante que puede o no ser crítico. `traceback` da detalles técnicos del error.
* **Limitaciones de Recursos:** Colab gratuito tiene límites. Para trabajos grandes/largos, considera dividir el trabajo o Colab Pro.
* **Actualización de Librerías:** `!pip install --upgrade seaborn` puede obtener la última versión si es necesario.