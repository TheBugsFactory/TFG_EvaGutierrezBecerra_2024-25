========================================================================
                        README - Script verificar_estado_sta.py
========================================================================

**Versión:** 1.0
**Fecha:** 2025-04-10
**Autor:** (Generado por IA - Gemini) - Adaptado de solicitud de usuario

------------------------------------------------------------------------
1. Idea / Objetivo
------------------------------------------------------------------------

El objetivo principal de este script de Python es **automatizar la verificación del estado de finalización de múltiples análisis de Abaqus**. Cuando se ejecutan varias simulaciones (archivos `.inp`), Abaqus genera archivos de estado (`.sta`) que indican si el análisis se completó con éxito o no. Revisar manualmente cada uno de estos archivos puede ser tedioso, especialmente con un gran número de simulaciones.

Este script busca todos los archivos `.sta` en su directorio, lee su contenido para encontrar los mensajes clave de finalización de Abaqus, y genera un archivo de texto resumen (`analysis_status.txt`) que lista cada simulación y su estado final (éxito, fallo/no completado, o desconocido).

Está diseñado para ser ejecutado fácilmente desde la interfaz de Abaqus/CAE usando la opción "Run Script".

------------------------------------------------------------------------
2. Funcionamiento
------------------------------------------------------------------------

Cuando se ejecuta el script (`verificar_estado_sta.py`) a través de Abaqus/CAE:

1.  **Identifica el Directorio:** Obtiene la ruta del directorio de trabajo actual (normalmente, donde se encuentra el script).
2.  **Busca Archivos `.sta`:** Utiliza el módulo `glob` de Python para encontrar todos los archivos que terminen con la extensión `.sta` en ese directorio.
3.  **Crea Carpeta de Salida:** Comprueba si existe una subcarpeta llamada `Status`. Si no existe, la crea. Si no puede crearla (p.ej., por problemas de permisos), informa del error y se detiene.
4.  **Prepara Archivo de Reporte:** Abre (o crea si no existe) un archivo llamado `analysis_status.txt` dentro de la carpeta `Status`. Este archivo se abre en modo escritura (`'w'`), lo que significa que **su contenido anterior se borrará** si el archivo ya existía. Escribe una cabecera en el archivo.
5.  **Procesa Cada `.sta`:** Itera sobre la lista de archivos `.sta` encontrados:
    * Extrae el nombre base del archivo (sin la extensión `.sta`), que se considera el nombre de la simulación.
    * Intenta abrir y leer el contenido completo del archivo `.sta`.
    * Busca dentro del contenido las frases exactas (incluyendo espacios iniciales):
        * `" THE ANALYSIS HAS COMPLETED SUCCESSFULLY"` (Éxito)
        * `" THE ANALYSIS HAS NOT BEEN COMPLETED"` (Fallo o No Completado)
    * Determina el estado basado en las frases encontradas:
        * Si encuentra la frase de éxito, el estado es "EJECUTADO CORRECTAMENTE".
        * Si encuentra la frase de fallo/no completado, el estado es "NO COMPLETADO O FALLIDO".
        * Si no encuentra ninguna de las dos, el estado es "ESTADO DESCONOCIDO".
    * Maneja posibles errores durante la lectura del archivo (p.ej., si el archivo está corrupto o no se puede acceder).
    * Escribe una línea en `analysis_status.txt` con el formato: `NombreSimulacion: Estado`.
6.  **Informa Progreso:** Durante la ejecución, imprime mensajes informativos en la consola (ventana de mensajes) de Abaqus/CAE, indicando qué directorio se está analizando, qué archivos se encuentran, qué archivo se está procesando y cuál es el resultado final. También informa de errores si ocurren.
7.  **Finaliza:** Una vez procesados todos los archivos `.sta`, cierra el archivo de reporte y muestra un mensaje final.

------------------------------------------------------------------------
3. Arquitectura del Sistema
------------------------------------------------------------------------

* **Tipo:** Script de Python independiente.
* **Entorno de Ejecución:** Diseñado para Abaqus/CAE (versión 6.12 o similar que use Python 2.6/2.7). Se ejecuta usando "File -> Run Script...".
* **Dependencias:**
    * **Python:** Versión 2.6 o 2.7 (la que incluye Abaqus 6.12).
    * **Módulos Python:** Solo utiliza módulos estándar de Python incluidos en la instalación base:
        * `os`: Para operaciones del sistema operativo (obtener directorio actual, crear carpetas, manejar rutas).
        * `glob`: Para encontrar archivos que coincidan con un patrón (`*.sta`).
        * `traceback`: Para obtener información detallada en caso de errores inesperados.
    * **No depende** de módulos específicos de la API de Abaqus (`abaqus`, `odbAccess`, `caeModules`, etc.) para su función principal, lo que lo hace relativamente simple y enfocado.
* **Entradas:** Archivos `.sta` presentes en el mismo directorio donde se ejecuta el script.
* **Salidas:**
    * Una subcarpeta llamada `Status` (creada si no existe).
    * Un archivo de texto `analysis_status.txt` dentro de la carpeta `Status`, conteniendo el resumen del estado de las simulaciones.
    * Mensajes de log/progreso en la ventana de mensajes de Abaqus/CAE.
* **Configuración:** Las frases clave de búsqueda, el nombre de la carpeta de salida y el nombre del archivo de reporte están definidos como constantes al principio del script para facilitar su modificación si fuera necesario.

Directorio_Trabajo/
|
|-- status_manager..py     <-- El script que ejecutas
|-- simulacion_A.inp            (Archivo de entrada de Abaqus, no usado por el script)
|-- simulacion_A.sta            <-- Archivo de estado que lee el script
|-- simulacion_A.odb            (Archivo de resultados, no usado por el script)
|-- simulacion_B.inp
|-- simulacion_B.sta            <-- Otro archivo de estado que lee el script
|-- simulacion_B.odb
|-- ... (otros archivos de Abaqus o del proyecto)
|
|-- Status/                     <-- Carpeta de Salida (Generada por el script si no existe)
    |
    |-- analysis_status.txt     <-- Archivo de Reporte (Generado/Sobrescrito por el script)
                                     (Contiene el estado de simulacion_A, simulacion_B, etc.)

------------------------------------------------------------------------
4. Consideraciones Adicionales
------------------------------------------------------------------------

* **Compatibilidad:** El script está escrito específicamente para la sintaxis de Python 2.6/2.7 usada en Abaqus 6.12. Versiones más recientes de Abaqus utilizan Python 3, por lo que el script necesitaría adaptaciones (p.ej., cambiar `print` a `print()`, posible manejo diferente de strings/bytes) para funcionar en ellas.
* **Ubicación del Script:** Es crucial que el archivo `.py` se encuentre en el mismo directorio que los archivos `.sta` que se desean verificar.
* **Exactitud de las Frases:** El script busca las cadenas de texto *exactas* proporcionadas por Abaqus. Si un análisis termina de forma muy abrupta o inusual, es posible que no escriba ninguna de estas frases en el archivo `.sta`, resultando en un estado "DESCONOCIDO".
* **Sobrescritura del Reporte:** Cada ejecución del script reemplaza el contenido del archivo `analysis_status.txt`. Si se necesita conservar historiales, se debería modificar el script para añadir datos (modo `'a'`) o generar nombres de archivo únicos (p.ej., con fecha y hora).
* **Manejo de Errores:** Se incluye manejo básico para errores de lectura/escritura de archivos. Sin embargo, problemas más complejos del sistema de archivos podrían no ser capturados elegantemente.
* **Rendimiento:** Para la mayoría de los casos, leer archivos `.sta` completos es rápido. Si se trabajara con un número masivo de archivos `.sta` extremadamente grandes (lo cual es poco común), se podría optimizar leyendo el archivo línea por línea desde el final, pero la implementación actual es más simple.
* **Codificación de Caracteres:** El script usa `# -*- coding: mbcs -*-`, común en entornos Windows para Abaqus. Si los nombres de archivo o las rutas contienen caracteres especiales fuera del ASCII estándar, podrían surgir problemas de codificación dependiendo del sistema operativo y su configuración. Usar `utf-8` podría ser más robusto si el entorno lo soporta adecuadamente.

========================================================================