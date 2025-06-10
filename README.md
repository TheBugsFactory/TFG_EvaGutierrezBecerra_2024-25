# TFG_EvaGutierrezBecerra_2024-25
Desarrollo y optimización de un modelo numérico de cabeza humana para estudios de impacto.

**Herramientas de Automatización para Post-Procesado de Simulaciones FEM (TFG)**

Este repositorio contiene un conjunto de herramientas desarrolladas en Python como parte de miTrabajo Fin De Grado (TFG), para automatizar el post-procesado de simulaciones de elementos finitos (FEM) realizadas en Abaqus. El objetivo principal es optimizar el flujo de trabajo, reducir el tiempo dedicado a tareas manuales y minimizar la probabilidad de errores.

**🎯 Necesidad de la Automatización**

El análisis de múltiples simulaciones FEM, genera un volumen considerable de datos. La gestión y el procesamiento manual de estos datos presentan varios desafíos:

- **Consumo de tiempo:** La revisión de estados, extracción de datos y generación de gráficos para cada simulación es una tarea laboriosa.
- **Propensión a errores:** Las tareas manuales repetitivas incrementan la posibilidad de cometer errores en la extracción, cálculo o interpretación de resultados.
- **Manejo de grandes volúmenes de datos:** Los archivos de salida de Abaqus (especialmente los `.odb`) pueden ser muy pesados, dificultando su manejo directo.

Para abordar estos problemas, se desarrollaron las siguientes herramientas de automatización.

**🛠️ Herramientas Desarrolladas**

Se han implementado tres scripts principales de Python, cada uno enfocado en una etapa específica del post-procesado:

1.  **_status_manager.py_**: Verifica el estado de finalización de las simulaciones.
2.  **_rpt_manager.py_**: Extrae datos primarios de los archivos `.odb` a formatos de texto más ligeros (`.rpt`).
3.  **_rpt_processor.py_**: Analiza los datos en formato `.rpt`, calcula magnitudes derivadas (como el HIC) y genera gráficos.

**🌊 Flujo de Trabajo General**

Las herramientas están diseñadas para trabajar en secuencia, creando un flujo de trabajo automatizado:
![Diagrama de Flujo Global](https://github.com/user-attachments/assets/15f34215-a7d8-432f-bdb8-654c24a84702)

 **📂 Estructura de Directorios Esperada**

Para el correcto funcionamiento de los scripts, se espera la siguiente organización de archivos y carpetas (algunas son generadas por los propios scripts):

``` plain text
PROYECTO_RAIZ/
├── simulaciones_abaqus/     <-- Contiene los archivos .odb y .sta de las simulaciones
│   ├── sim_A_v10/
│   │   ├── sim_A_v10.odb
│   │   └── sim_A_v10.sta
│   ├── sim_B_v20/
│   │   ├── sim_B_v20.odb
│   │   └── sim_B_v20.sta
│   └── ...
├── status_manager.py
├── rpt_manager.py
├── rpt_processor.py
├── Status/                  <-- Generada por status_manager.py
│   └── analysis_status.txt
├── Reports/                 <-- Generada por rpt_manager.py
│   ├── sim_A_v10/
│   │   ├── Pressure_..._mean.rpt
│   │   ├── A1_Acc_mean.rpt
│   │   └── ...
│   └── sim_B_v20/
│       └── ...
└── Results/                 <-- Generada por rpt_processor.py
    ├── sim_A_v10/
    │   ├── Pressure_vs_Time.png
    │   ├── Acceleration_Magnitude_vs_Time.png
    │   └── ...
    ├── sim_B_v20/
    │   └── ...
    ├── HIC15_vs_Impact_Speed.png
    ├── Max_HIC_PLA_vs_Impact_Speed.png
    └── ...
```

_**Nota**_: Inicialmente, los scripts `status_manager.py` y `rpt_manager.py` se ejecutan desde el directorio que contiene los archivos `.odb` y `.sta` (e.g., dentro de `simulaciones_abaqus/` o copiándolos al directorio raíz donde están los scripts).

**⚙️ Requisitos**

*   **Para `status_manager.py` y `rpt_manager.py`:**
    *   Abaqus/CAE (probado con v6.12, que incluye un intérprete Python 2.x embebido).
*   **Para `rpt_processor.py`:**
    *   Python 3.x.
    *   Librerías de Python:
        *   NumPy
        *   Matplotlib
        *   Seaborn
        ```bash
        pip install numpy matplotlib seaborn
        ```

**🚀 Uso General**

El flujo de trabajo general implica ejecutar los scripts en el orden presentado. Los dos primeros scripts (`status_manager.py` y `rpt_manager.py`) dependen del entorno Abaqus/CAE, mientras que el tercero (`rpt_processor.py`) puede ejecutarse en cualquier entorno Python 3 estándar, incluyendo Google Colab.

1.  **Preparación Inicial (Entorno Local con Abaqus):**
    *   Organiza tus archivos de simulación de Abaqus (`.odb`, `.sta`) en un directorio de trabajo en tu máquina local.
    *   Copia los scripts `status_manager.py` y `rpt_manager.py` a este directorio.

2.  **Verificar Estado (`status_manager.py`) - Entorno Abaqus/CAE:**
    *   Abre Abaqus/CAE.
    *   Ve a `File -> Set Working Directory...` y selecciona tu directorio de trabajo.
    *   Ve a `File -> Run Script...` y selecciona `status_manager.py`.
    *   Se generará el archivo `Status/analysis_status.txt` con el resumen del estado de las simulaciones. Revisa este archivo.

3.  **Extraer Datos (`rpt_manager.py`) - Entorno Abaqus/CAE:**
    *   **Importante:** Antes de ejecutar, abre `rpt_manager.py` con un editor de texto y modifica los valores de las variables `INSTANCE_NAME`, `STEP_NAME`, `ELEMENT_SETS_PRESSURE`, y `NODE_SET_ACC` para que coincidan con los nombres exactos utilizados en tu modelo de Abaqus.
    *   Desde Abaqus/CAE (con el directorio de trabajo ya configurado), ve a `File -> Run Script...` y selecciona `rpt_manager.py`.
    *   Esto creará la carpeta `Reports/` en tu directorio de trabajo. Dentro de `Reports/`, se generarán subcarpetas para cada archivo `.odb` procesado, conteniendo los archivos `.rpt` con los datos extraídos.

4.  **Procesar Datos y Generar Gráficos (`rpt_processor.py`) - Entorno Python 3:**
    Este script es independiente de Abaqus y se ejecuta con Python 3. Tienes varias opciones para ejecutarlo:

    *   **Opción A: Ejecución Local (Terminal/IDE):**
        *   Asegúrate de tener Python 3 y las librerías necesarias (NumPy, Matplotlib, Seaborn) instaladas en tu sistema.
            ```bash
            pip install numpy matplotlib seaborn
            ```
        *   Copia el script `rpt_processor.py` al directorio que contiene la carpeta `Reports/` (generalmente el directorio raíz de tu proyecto donde ya tienes `Status/` y `Reports/`).
        *   Abre una terminal o línea de comandos en ese directorio.
        *   Ejecuta el script:
            ```bash
            python rpt_processor.py
            ```
        *   Si el script no puede deducir la velocidad de impacto del nombre de las carpetas en `Reports/` (e.g., `sim_A_v10` para 10 m/s), te pedirá que la introduzcas manualmente.
        *   Los resultados y gráficos se guardarán en una nueva carpeta `Results/`.

    *   **Opción B: Ejecución en Google Colab (Sincronizando con Google Drive):**
        *   **Preparación en Google Drive:**
            *   Sube toda la estructura de tu proyecto a Google Drive, manteniendo la organización de carpetas. Es decir, tu carpeta raíz del proyecto en Drive debería contener:
                *   El script `rpt_processor.py`.
                *   La carpeta `Reports/` (generada en el paso 3) con todas sus subcarpetas y archivos `.rpt`.
        *   **En Google Colab:**
            1.  Crea un nuevo notebook en Google Colab.
            2.  Monta tu Google Drive para acceder a los archivos:
                ```python
                from google.colab import drive
                drive.mount('/content/drive')
                ```
                Sigue las instrucciones para autorizar el acceso.
            3.  Navega al directorio de tu proyecto en Google Drive usando el comando `cd` en una celda de código. Por ejemplo:
                ```python
                %cd /content/drive/MyDrive/Ruta/A/Tu/Proyecto_Raiz/
                ```
                (Reemplaza `Ruta/A/Tu/Proyecto_Raiz/` con la ruta real a tu carpeta).
            4.  Asegúrate de que las librerías necesarias estén instaladas en el entorno de Colab (generalmente ya lo están, pero puedes forzar la instalación si es necesario):
                ```python
                !pip install numpy matplotlib seaborn
                ```
            5.  Ejecuta el script `rpt_processor.py`:
                ```python
                !python rpt_processor.py
                ```
            6.  Si el script solicita la velocidad de impacto, la pedirá en la salida de la celda.
            7.  La carpeta `Results/` con los gráficos y resultados se creará dentro de tu carpeta de proyecto en Google Drive.

Independientemente de la opción elegida para ejecutar `rpt_processor.py`, los resultados finales (gráficos individuales y agregados) se encontrarán en la carpeta `Results/`.

**💡 Consideraciones y Mejoras Futuras**

*   **Externalización de configuración para `rpt_manager.py`:** Modificar `rpt_manager.py` para leer los nombres de Sets, instancia y paso desde un archivo de configuración externo (e.g., `.ini` o `.txt`) en lugar de tenerlos "hard-coded". Esto mejoraría enormemente su reusabilidad.
*   **Entrada de velocidad para `rpt_processor.py`:** Mejorar el sistema de obtención de velocidad, quizás mediante un archivo de metadatos asociado a cada simulación o una opción para pasar las velocidades como argumento al script, para evitar la entrada manual si el nombrado de carpetas no sigue el patrón esperado o para flujos completamente automatizados.
*   **Interfaz Gráfica de Usuario (GUI):** Para usuarios menos familiarizados con la línea de comandos o Abaqus Scripting, una GUI podría simplificar el uso, especialmente para el script `rpt_processor.py`.
