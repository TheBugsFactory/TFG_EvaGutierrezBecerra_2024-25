=============================================
Análisis y Corrección de Datos de Simulación
vs. Datos Experimentales (Nahum)
=============================================

1. OBJETIVO DEL SCRIPT
----------------------
Este script tiene como objetivo principal comparar datos biomecánicos obtenidos de simulaciones computacionales con datos experimentales de referencia (Nahum et al.).

Busca:
- Identificar errores sistemáticos en los resultados de la simulación.
- Desarrollar un modelo de corrección lineal para mitigar dichos errores.
- Validar la efectividad de esta corrección.

Métricas analizadas:
- Aceleración de la cabeza
- Presiones de golpe (coup) y contragolpe (contrecoup)
- Tiempo hasta el pico de la señal


2. ¿QUÉ HACE EL SCRIPT?
-----------------------
El script realiza las siguientes acciones de forma secuencial:

Configuración Inicial:
- Define rutas a los archivos de entrada y a la carpeta de resultados.
- Crea la carpeta de resultados si no existe.

Carga y Preprocesamiento de Datos:
- Lee los archivos CSV de aceleración y presión.
- Convierte las columnas relevantes a formato numérico.
- Fusiona ambos DataFrames por número de ensayo (N_Ensayo).
- Calcula los ratios Nahum/Simulación para cada métrica.

Análisis del Error Sistemático (Fase 1):
- Genera gráficos de dispersión de los valores originales por métrica.
- Visualiza la variación de los ratios según la velocidad de impacto.

Desarrollo del Modelo de Corrección (Fase 2):
- Realiza regresiones lineales entre datos experimentales y de simulación.
- Guarda los parámetros obtenidos (pendiente, intercepto, R², p-valor).

Aplicación y Validación de la Corrección (Fase 3):
- Aplica la corrección lineal a los datos simulados.
- Compara los valores corregidos con los experimentales.
- Calcula y guarda el Error Absoluto Porcentual Medio (MAPE) antes y después de la corrección.

Guardado de Resultados:
- Guarda todos los gráficos generados en formatos PNG y EPS.
- Guarda tablas con datos originales, corregidos y experimentales en TXT y CSV.
- Exporta un CSV con el DataFrame completo.


3. ¿CÓMO LO HACE?
-----------------
Librerías utilizadas:
- pandas: manipulación de datos
- numpy: operaciones numéricas
- matplotlib: generación de gráficos
- scipy.stats.linregress: regresión lineal
- os: manejo de rutas y carpetas

Flujo de trabajo:
1. Preparación: carga, limpieza y fusión de datos.
2. Visualización inicial: gráficos comparativos.
3. Modelado: regresión lineal para obtener correcciones.
4. Aplicación: ajuste de los datos simulados.
5. Evaluación: MAPE y gráficos post-corrección.
6. Reporte: exportación de resultados para análisis posterior.


4. CONFIGURACIÓN Y VARIABLES A EDITAR
-------------------------------------
Antes de ejecutar el script, revisar la sección --- Configuración --- y modificar las siguientes variables según sea necesario:

ACCELERATION_DATA_FILE
Ruta al archivo CSV de aceleración.
Ejemplo:
'/content/drive/MyDrive/Beca Colaboracion 2024-2025/02_Validacion del modelo/datos_aceleracion.csv'

PRESSURE_DATA_FILE
Ruta al archivo CSV de presión.
Ejemplo:
'/content/drive/MyDrive/Beca Colaboracion 2024-2025/02_Validacion del modelo/datos_presion.csv'

RESULTS_FOLDER
Carpeta donde se guardarán los resultados.
Ejemplo:
'/content/drive/MyDrive/Beca Colaboracion 2024-2025/02_Validacion del modelo/resultados_analisis_correcion'

Si la carpeta no existe, se creará automáticamente.

Columnas esperadas en los CSV:

cols_accel:
['N_Ensayo', 'F_impacto_kN', 'Energia_J', 'v_cabeza_m_s',
 'Acc_Nahum_m_s2', 'Acc_Sim_m_s2', 'T_pico_Nahum_ms', 'T_pico_Sim_ms']

cols_pressure:
['N_Ensayo', 'F_impacto_kN', 'Energia_J', 'v_cabeza_m_s',
 'PCoup_Nahum_mmHg', 'PCoup_Sim_mmHg', 'PContrecoup_Nahum_mmHg', 'PContrecoup_Sim_mmHg']

Formato de carga en load_and_preprocess_data():
- Separador: sep=';'
- Decimal: decimal=','
- Valores nulos: na_values=['---', '']


5. CONSIDERACIONES ADICIONALES
------------------------------
Dependencias:
Asegúrate de tener instaladas las siguientes bibliotecas:

pip install pandas numpy matplotlib scipy

Ejecución en Google Colab:
El script incluye una comprobación para montar Google Drive si se detecta que se ejecuta en Colab.

Manejo de errores:
- Archivos no encontrados o con formato incorrecto generan advertencias.
- Si hay pocos datos válidos, la regresión puede no realizarse.

Interpretación de resultados:
- R² (R-cuadrado): representa el ajuste del modelo. Valores cercanos a 1 son deseables.
- P-valor: si es menor a 0.05, la relación entre variables es estadísticamente significativa.

Limitaciones del modelo:
El modelo de corrección es lineal. Si la relación entre los datos no lo es, puede que no sea adecuado.

Presión de contragolpe (PContrecoup):
- Para ratios y gráficos originales se usan los valores absolutos.
- Para regresión y corrección se usan los valores con signo.
- El MAPE se calcula sobre valores absolutos antes y después de aplicar la corrección.

Salida gráfica:
Los gráficos se exportan en formato PNG (ráster) y EPS (vectorial) para diferentes usos.

