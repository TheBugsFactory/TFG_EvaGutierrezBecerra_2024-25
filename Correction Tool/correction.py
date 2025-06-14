import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import os
import glob
import re
import traceback

# --- Configuración ---
# Rutas de los archivos de entrada para DERIVAR parámetros de corrección (datos resumidos)
ACCELERATION_DATA_FILE = '/content/drive/MyDrive/Beca Colaboracion 2024-2025/02_Validacion del modelo/datos_aceleracion.csv'
PRESSURE_DATA_FILE = '/content/drive/MyDrive/Beca Colaboracion 2024-2025/02_Validacion del modelo/datos_presion.csv'

# Carpeta para guardar los resultados del ANÁLISIS Y VALIDACIÓN INICIAL de datos resumidos
RESULTS_FOLDER = '/content/drive/MyDrive/Beca Colaboracion 2024-2025/02_Validacion del modelo/resultados_analisis_correcion'

# --- NUEVA CONFIGURACIÓN PARA CORRECCIÓN DE ARCHIVOS .RPT ---
# Carpeta raíz donde se encuentran los directorios de cada simulación
REPORTS_ROOT_DIR_FOR_CORRECTION = '/content/drive/MyDrive/Beca Colaboracion 2024-2025/10_Resultados Simulaciones/Reports_Nahum_v3'

# Nombres base de los archivos .rpt a procesar
ACCEL_COMPONENT_RPT_FILES = ['A1_Acc_mean.rpt', 'A2_Acc_mean.rpt', 'A3_Acc_mean.rpt']
# Nombre del archivo de salida para la magnitud de aceleración corregida
OUTPUT_MAGNITUDE_ACCEL_FIXED_RPT_FILE = 'Magnitude_Acc_mean_fixed.rpt'

PCOUP_RPT_FILE = 'Pressure_FRONTREF_mean.rpt'
PCONTRECOUP_RPT_FILE = 'Pressure_BACKREF_mean.rpt'

# --- Fin de Nueva Configuración ---

# Crear la carpeta de resultados del análisis si no existe
if not os.path.exists(RESULTS_FOLDER):
    os.makedirs(RESULTS_FOLDER)
    print(f"Carpeta '{RESULTS_FOLDER}' creada.")

# Columnas esperadas en los CSV de datos resumidos (para derivar params)
cols_accel = [
    'N_Ensayo', 'F_impacto_kN', 'Energia_J', 'v_cabeza_m_s',
    'Acc_Nahum_m_s2', 'Acc_Sim_m_s2', # Acc_Sim_m_s2 DEBE ser la magnitud de la aceleración
    'T_pico_Nahum_ms', 'T_pico_Sim_ms'
]
cols_pressure = [
    'N_Ensayo', 'F_impacto_kN', 'Energia_J', 'v_cabeza_m_s',
    'PCoup_Nahum_mmHg', 'PCoup_Sim_mmHg',
    'PContrecoup_Nahum_mmHg', 'PContrecoup_Sim_mmHg'
]

# --- Funciones de Análisis de Datos Resumidos (sin cambios) ---
def load_and_preprocess_data():
    # ... (código igual que antes)
    """Carga los datos de los archivos CSV y realiza un preprocesamiento básico."""
    try:
        df_accel = pd.read_csv(ACCELERATION_DATA_FILE,
                               usecols=cols_accel,
                               na_values=['---', ''],
                               sep=';',
                               decimal=',')
        df_pressure = pd.read_csv(PRESSURE_DATA_FILE,
                                  usecols=cols_pressure,
                                  na_values=['---', ''],
                                  sep=';',
                                  decimal=',')
        print("Archivos CSV de datos resumidos leídos correctamente.")
    except FileNotFoundError as e:
        print(f"Error: Archivo de datos resumidos no encontrado - {e.filename}")
        print(f"Asegúrate de que los archivos CSV '{ACCELERATION_DATA_FILE}' y '{PRESSURE_DATA_FILE}' estén en las rutas especificadas.")
        return None
    except ValueError as e:
        print(f"Error al leer CSV de datos resumidos: {e}")
        print("Verifica que los nombres de las columnas en los CSV coincidan y el formato de números sea correcto.")
        return None
    except Exception as e:
        print(f"Un error inesperado ocurrió al cargar los datos resumidos: {e}")
        return None

    print("Convirtiendo columnas de datos resumidos a numérico...")
    for col in df_accel.columns:
        if col not in ['N_Ensayo']:
             df_accel[col] = pd.to_numeric(df_accel[col], errors='coerce')
    for col in df_pressure.columns:
        if col not in ['N_Ensayo']:
            df_pressure[col] = pd.to_numeric(df_pressure[col], errors='coerce')
    print("Conversión a numérico completada.")

    print("Fusionando DataFrames de datos resumidos...")
    df_accel['N_Ensayo'] = df_accel['N_Ensayo'].astype(str)
    df_pressure['N_Ensayo'] = df_pressure['N_Ensayo'].astype(str)
    try:
        df_merged = pd.merge(df_accel, df_pressure, on='N_Ensayo', suffixes=('_acc', '_pres'))
    except Exception as e:
        print(f"Error al fusionar DataFrames de datos resumidos: {e}")
        return None
    print("DataFrames de datos resumidos fusionados.")

    cols_to_drop = []
    renamed_cols = {}
    for col in df_merged.columns:
        if col.endswith('_pres'):
            base_col_name = col[:-5]
            if f"{base_col_name}_acc" in df_merged.columns:
                cols_to_drop.append(col)
            else:
                renamed_cols[col] = base_col_name
        elif col.endswith('_acc'):
            renamed_cols[col] = col[:-4]
    df_merged = df_merged.drop(columns=cols_to_drop)
    df_merged = df_merged.rename(columns=renamed_cols)

    print("Calculando ratios para datos resumidos...")
    df_merged['Ratio_Acc'] = np.where((df_merged['Acc_Sim_m_s2'] != 0) & (df_merged['Acc_Nahum_m_s2'].notna()),
                                     df_merged['Acc_Nahum_m_s2'] / df_merged['Acc_Sim_m_s2'], np.nan)
    df_merged['Ratio_PCoup'] = np.where((df_merged['PCoup_Sim_mmHg'] != 0) & (df_merged['PCoup_Nahum_mmHg'].notna()),
                                       df_merged['PCoup_Nahum_mmHg'] / df_merged['PCoup_Sim_mmHg'], np.nan)
    df_merged['Ratio_PContrecoup'] = np.where(
        (df_merged['PContrecoup_Sim_mmHg'] != 0) & (df_merged['PContrecoup_Nahum_mmHg'].notna()),
        df_merged['PContrecoup_Nahum_mmHg'].abs() / df_merged['PContrecoup_Sim_mmHg'].abs(), np.nan)
    df_merged['Ratio_Tpico'] = np.where((df_merged['T_pico_Sim_ms'] != 0) & (df_merged['T_pico_Nahum_ms'].notna()),
                                     df_merged['T_pico_Nahum_ms'] / df_merged['T_pico_Sim_ms'], np.nan)
    print("Cálculo de ratios para datos resumidos completado.")
    print("\n--- Datos Resumidos Cargados y Preprocesados (primeras 5 filas) ---")
    print(df_merged.head())
    return df_merged

def plot_scatter_comparison(df, sim_col, nahum_col, title_prefix, metric_unit, filename_suffix):
    # ... (código igual que antes)
    """Genera un gráfico de dispersión y lo guarda en PNG y EPS."""
    plt.figure(figsize=(10, 7))
    valid_data = df[[sim_col, nahum_col]].dropna()
    title = f'{title_prefix}: Nahum vs. Simulación (Original)'
    xlabel = f'Simulación ({metric_unit})'
    ylabel = f'Nahum ({metric_unit})'

    base_filename = os.path.join(RESULTS_FOLDER, f'scatter_{filename_suffix}_original')
    filename_png = f"{base_filename}.png"
    filename_eps = f"{base_filename}.eps"

    if valid_data.empty:
        print(f"ADVERTENCIA: No hay datos válidos para graficar: {title}")
        # ... (código de ploteo vacío igual que antes)
        plt.text(0.5, 0.5, 'No hay datos válidos', ha='center', va='center', fontsize=12, color='red')
        plt.title(title, fontsize=16)
        plt.xlabel(xlabel, fontsize=14)
        plt.ylabel(ylabel, fontsize=14)
        plt.grid(True)
        plt.savefig(filename_png)
        plt.savefig(filename_eps, format='eps', bbox_inches='tight')
        plt.close()
        print(f"Gráficos vacíos guardados en: {filename_png} y {filename_eps}")
        return None

    plt.scatter(valid_data[sim_col], valid_data[nahum_col], label='Datos Originales', s=60, edgecolors='k', alpha=0.75)
    min_val = min(valid_data[sim_col].min(), valid_data[nahum_col].min()) * 0.85
    max_val = max(valid_data[sim_col].max(), valid_data[nahum_col].max()) * 1.15
    plt.plot([min_val, max_val], [min_val, max_val], 'k--', lw=1.5, label='Y=X (Referencia Ideal)')

    plt.title(title, fontsize=16, fontweight='bold')
    plt.xlabel(xlabel, fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    plt.legend(fontsize=12)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig(filename_png)
    plt.savefig(filename_eps, format='eps', bbox_inches='tight')
    plt.close()
    print(f"Gráficos guardados en: {filename_png} y {filename_eps}")
    return valid_data

def plot_ratio_vs_severity(df, ratio_col, severity_col, title_prefix, ratio_name, severity_name_unit, filename_suffix):
    # ... (código igual que antes)
    """Genera un gráfico de ratio vs severidad y lo guarda en PNG y EPS."""
    plt.figure(figsize=(10, 7))
    valid_data = df[[ratio_col, severity_col]].dropna()
    title = f'{title_prefix} ({ratio_name}) vs. {severity_name_unit}'
    xlabel = severity_name_unit
    ylabel = f'Ratio {ratio_name} (Nahum/Sim)'

    base_filename = os.path.join(RESULTS_FOLDER, f'ratio_{filename_suffix}_vs_severidad')
    filename_png = f"{base_filename}.png"
    filename_eps = f"{base_filename}.eps"

    if valid_data.empty:
        print(f"ADVERTENCIA: No hay datos válidos para graficar: {title}")
        # ... (código de ploteo vacío igual que antes)
        plt.text(0.5, 0.5, 'No hay datos válidos', ha='center', va='center', fontsize=12, color='red')
        plt.title(title, fontsize=16)
        plt.xlabel(xlabel, fontsize=14)
        plt.ylabel(ylabel, fontsize=14)
        plt.grid(True)
        plt.savefig(filename_png)
        plt.savefig(filename_eps, format='eps', bbox_inches='tight')
        plt.close()
        print(f"Gráficos vacíos guardados en: {filename_png} y {filename_eps}")
        return

    plt.scatter(valid_data[severity_col], valid_data[ratio_col], s=60, edgecolors='k', alpha=0.75)
    mean_ratio = valid_data[ratio_col].mean()
    plt.axhline(y=mean_ratio, color='crimson', linestyle='--', lw=1.5, label=f'Media Ratio: {mean_ratio:.2f}')
    plt.title(title, fontsize=16, fontweight='bold')
    plt.xlabel(xlabel, fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    plt.legend(fontsize=12)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig(filename_png)
    plt.savefig(filename_eps, format='eps', bbox_inches='tight')
    plt.close()
    print(f"Gráficos guardados en: {filename_png} y {filename_eps}")

def linear_regression_correction(valid_data, sim_col, nahum_col, metric_name):
    # ... (código igual que antes)
    """Realiza regresión lineal y devuelve los parámetros."""
    if valid_data is None or len(valid_data) < 2:
        print(f"ADVERTENCIA: No hay suficientes datos válidos para la regresión de {metric_name}.")
        return None
    slope, intercept, r_value, p_value, std_err = stats.linregress(valid_data[sim_col], valid_data[nahum_col])
    r_squared = r_value**2
    result = {'slope': slope, 'intercept': intercept, 'r_squared': r_squared, 'p_value': p_value, 'std_err': std_err, 'name': metric_name,
              'equation': f"{nahum_col} = {slope:.4e} * {sim_col} + {intercept:.2f}"}
    print(f"\n--- Regresión Lineal para {metric_name} ---")
    print(f"  Ecuación: {result['equation']}")
    print(f"  R-cuadrado (R²): {r_squared:.4f}")
    print(f"  P-valor (pendiente): {p_value:.4f}")
    if p_value > 0.05: print(f"  ADVERTENCIA: P-valor > 0.05, relación lineal podría no ser significativa.")
    if r_squared < 0.5: print(f"  NOTA: R-cuadrado < 0.5, el modelo lineal explica poca varianza.")
    return result

def apply_correction(df, sim_col, correction_params, corrected_col_name):
    # ... (código igual que antes)
    """Aplica la corrección lineal a una columna de un DataFrame (para datos resumidos)."""
    if correction_params and isinstance(correction_params, dict):
        df[corrected_col_name] = correction_params['slope'] * df[sim_col] + correction_params['intercept']
    else:
        print(f"ADVERTENCIA: No se aplicó corrección para '{corrected_col_name}' en datos resumidos.")
        df[corrected_col_name] = df[sim_col] # o np.nan si se prefiere no propagar el original
    return df

def plot_corrected_scatter(df, corrected_sim_col, nahum_col, title_prefix, metric_unit, filename_suffix):
    # ... (código igual que antes)
    """Genera un gráfico de dispersión de datos corregidos y lo guarda en PNG y EPS."""
    plt.figure(figsize=(10, 7))
    valid_data = df[[corrected_sim_col, nahum_col]].dropna()
    title = f'{title_prefix}: Nahum vs. Simulación Corregida'
    xlabel = f'Simulación Corregida ({metric_unit})'
    ylabel = f'Nahum ({metric_unit})'

    base_filename = os.path.join(RESULTS_FOLDER, f'scatter_{filename_suffix}_corregido')
    filename_png = f"{base_filename}.png"
    filename_eps = f"{base_filename}.eps"

    if valid_data.empty:
        print(f"ADVERTENCIA: No hay datos válidos para graficar (corregidos): {title}")
        # ... (código de ploteo vacío igual que antes)
        plt.text(0.5, 0.5, 'No hay datos válidos', ha='center', va='center', fontsize=12, color='red')
        plt.title(title, fontsize=16)
        plt.xlabel(xlabel, fontsize=14)
        plt.ylabel(ylabel, fontsize=14)
        plt.grid(True)
        plt.savefig(filename_png)
        plt.savefig(filename_eps, format='eps', bbox_inches='tight')
        plt.close()
        print(f"Gráficos vacíos guardados en: {filename_png} y {filename_eps}")
        return

    plt.scatter(valid_data[corrected_sim_col], valid_data[nahum_col], color='forestgreen', label='Datos Corregidos vs. Nahum', s=60, edgecolors='k', alpha=0.75)
    min_val = min(valid_data[corrected_sim_col].min(), valid_data[nahum_col].min()) * 0.85
    max_val = max(valid_data[corrected_sim_col].max(), valid_data[nahum_col].max()) * 1.15
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', lw=1.5, label='Y=X (Objetivo Ideal)')
    plt.title(title, fontsize=16, fontweight='bold')
    plt.xlabel(xlabel, fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    plt.legend(fontsize=12)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig(filename_png)
    plt.savefig(filename_eps, format='eps', bbox_inches='tight')
    plt.close()
    print(f"Gráficos guardados en: {filename_png} y {filename_eps}")

def calculate_mape(y_true, y_pred):
    # ... (código igual que antes)
    """Calcula el Mean Absolute Percentage Error."""
    y_true_pd = pd.Series(y_true).copy()
    y_pred_pd = pd.Series(y_pred).copy()
    valid_idx = y_true_pd.notna() & y_pred_pd.notna()
    y_true_filt = y_true_pd[valid_idx]
    y_pred_filt = y_pred_pd[valid_idx]
    non_zero_true_idx = y_true_filt != 0
    if not non_zero_true_idx.any(): return np.nan
    y_true_final = y_true_filt[non_zero_true_idx]
    y_pred_final = y_pred_filt[non_zero_true_idx]
    if len(y_true_final) == 0: return np.nan
    return np.mean(np.abs((y_true_final - y_pred_final) / y_true_final)) * 100

# --- FUNCIÓN ADAPTADA PARA LEER .RPT (sin cambios) ---
def read_rpt_file_for_correction(filepath: str):
    """
    Lee un archivo .rpt esperando columnas de tiempo y valor.
    Devuelve un DataFrame de Pandas con columnas 'Time' y 'Value_Original' o None si falla.
    """
    time_values = []
    data_values = []
    data_pattern = re.compile(r"^\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s+([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)")
    header_skip_pattern = re.compile(r"^\s*\*\*|^\s*X\s+PLOT")

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        for line_num, line_content in enumerate(lines):
            line_stripped = line_content.strip()
            if not line_stripped or header_skip_pattern.match(line_stripped):
                continue
            match_data = data_pattern.match(line_stripped)
            if match_data:
                try:
                    time_str = match_data.group(1)
                    data_val_str = match_data.group(2)
                    current_time = float(time_str)
                    current_data_val = float(data_val_str)
                    time_values.append(current_time)
                    data_values.append(current_data_val)
                except (ValueError, IndexError) as e_parse:
                    print(f"    WARN (read_rpt): Error al parsear datos en línea {line_num + 1} de {os.path.basename(filepath)} ('{line_stripped}'): {e_parse}. Omitiendo línea.")
        if not time_values or not data_values:
            print(f"    ERROR (read_rpt): No se encontraron pares de datos tiempo-valor válidos en {os.path.basename(filepath)}.")
            return None
        df_rpt = pd.DataFrame({'Time': time_values, 'Value_Original': data_values})
        return df_rpt
    except FileNotFoundError:
        return None # Será manejado en la función llamadora
    except Exception as e_read:
        print(f"  ERROR (read_rpt): Error inesperado al leer el archivo {os.path.basename(filepath)}: {e_read}")
        traceback.print_exc()
        return None

# --- FUNCIÓN PRINCIPAL MODIFICADA PARA PROCESAR ARCHIVOS .RPT POR DIRECTORIO ---
def process_simulation_rpts_in_directory_structure(
    reports_root_folder,
    params_accel,
    params_pcoup,
    params_pcontrecoup):
    """
    Busca directorios de simulación. En cada uno:
    1. Lee componentes de aceleración, calcula magnitud.
    2. Corrige la magnitud de aceleración y las presiones.
    3. Guarda los archivos corregidos.
    """
    print(f"\n\n=== FASE 4: APLICACIÓN DE CORRECCIÓN A ARCHIVOS .RPT EN '{reports_root_folder}' ===")
    if not os.path.isdir(reports_root_folder):
        print(f"Error: La carpeta raíz de reportes '{reports_root_folder}' no existe.")
        return

    try:
        simulation_dirs = [d for d in os.listdir(reports_root_folder)
                           if os.path.isdir(os.path.join(reports_root_folder, d))]
    except Exception as e:
        print(f"Error al listar directorios en '{reports_root_folder}': {e}")
        return

    if not simulation_dirs:
        print(f"No se encontraron directorios de simulación en '{reports_root_folder}'.")
        return

    print(f"Se encontraron {len(simulation_dirs)} directorios de simulación para procesar.")
    total_files_processed_accel_mag = 0
    total_files_processed_pressure = 0
    total_files_corrected = 0

    # Constantes de conversión de unidades
    MM_S2_TO_M_S2 = 0.001
    M_S2_TO_MM_S2 = 1000.0
    MPA_TO_MMHG = 7500.62
    MMHG_TO_MPA = 1.0 / MPA_TO_MMHG

    for sim_dir_name in simulation_dirs:
        sim_dir_path = os.path.join(reports_root_folder, sim_dir_name)
        print(f"\nProcesando simulación en directorio: {sim_dir_path}")

        # --- Procesar y Corregir Magnitud de Aceleración ---
        if params_accel:
            accel_components_data = {}
            time_vector_ref = None
            components_ok = True

            for comp_file_base in ACCEL_COMPONENT_RPT_FILES:
                comp_file_path = os.path.join(sim_dir_path, comp_file_base)
                if not os.path.exists(comp_file_path):
                    print(f"    AVISO: Archivo de componente de aceleración {comp_file_base} no encontrado en {sim_dir_name}. No se puede calcular magnitud.")
                    components_ok = False
                    break
                
                df_comp = read_rpt_file_for_correction(comp_file_path)
                if df_comp is None or df_comp.empty:
                    print(f"    AVISO: No se pudieron leer datos del componente {comp_file_base}. No se puede calcular magnitud.")
                    components_ok = False
                    break

                # Guardar datos del componente (original en mm/s^2)
                component_key = comp_file_base.split('_')[0] # A1, A2, A3
                accel_components_data[component_key] = df_comp['Value_Original'].values # en mm/s^2

                if time_vector_ref is None:
                    time_vector_ref = df_comp['Time'].values
                elif len(time_vector_ref) != len(df_comp['Time'].values) or \
                     not np.allclose(time_vector_ref, df_comp['Time'].values, atol=1e-7, rtol=1e-7): # Tolerancia para comparación de flotantes
                    print(f"    ERROR: Vectores de tiempo no coinciden entre componentes de aceleración en {sim_dir_name}. No se puede calcular magnitud.")
                    components_ok = False
                    break
            
            if components_ok and time_vector_ref is not None and \
               all(key in accel_components_data for key in ['A1', 'A2', 'A3']):
                total_files_processed_accel_mag += 1
                print(f"  Calculando magnitud de aceleración para {sim_dir_name}...")
                
                # Convertir componentes a m/s^2 para cálculo de magnitud y corrección
                a1_m_s2 = accel_components_data['A1'] * MM_S2_TO_M_S2
                a2_m_s2 = accel_components_data['A2'] * MM_S2_TO_M_S2
                a3_m_s2 = accel_components_data['A3'] * MM_S2_TO_M_S2
                
                magnitude_accel_m_s2 = np.sqrt(a1_m_s2**2 + a2_m_s2**2 + a3_m_s2**2)
                
                # Aplicar corrección a la magnitud (que está en m/s^2)
                slope = params_accel['slope']
                intercept = params_accel['intercept']
                magnitude_accel_corrected_m_s2 = slope * magnitude_accel_m_s2 + intercept
                
                # Convertir magnitud corregida de nuevo a mm/s^2 para guardar
                magnitude_accel_corrected_rpt_unit = magnitude_accel_corrected_m_s2 * M_S2_TO_MM_S2
                
                # Crear DataFrame para guardar
                df_magnitude_corrected = pd.DataFrame({
                    'Time': time_vector_ref,
                    'Corrected_Magnitude_Acc_mm_s2': magnitude_accel_corrected_rpt_unit
                })
                
                output_rpt_path = os.path.join(sim_dir_path, OUTPUT_MAGNITUDE_ACCEL_FIXED_RPT_FILE)
                try:
                    df_magnitude_corrected.to_csv(output_rpt_path, sep=' ', header=False, index=False, float_format='%.6e')
                    print(f"    Magnitud de aceleración corregida guardada en: {OUTPUT_MAGNITUDE_ACCEL_FIXED_RPT_FILE}")
                    total_files_corrected += 1
                except Exception as e_save:
                    print(f"    ERROR al guardar magnitud de aceleración corregida '{OUTPUT_MAGNITUDE_ACCEL_FIXED_RPT_FILE}': {e_save}")
            elif components_ok : # pero algo falló con los datos
                 print(f"    INFO: No se procesó la magnitud de aceleración para {sim_dir_name} debido a falta de datos o inconsistencias.")

        else: # params_accel es None
            print(f"  ADVERTENCIA: No hay parámetros de corrección para Aceleración. Se omitirá el cálculo y corrección de magnitud.")

        # --- Procesar archivo de Presión Coup ---
        if params_pcoup and PCOUP_RPT_FILE:
            rpt_file_path = os.path.join(sim_dir_path, PCOUP_RPT_FILE)
            if os.path.exists(rpt_file_path):
                total_files_processed_pressure += 1
                print(f"  Procesando archivo de Presión Coup: {PCOUP_RPT_FILE}")
                df_rpt = read_rpt_file_for_correction(rpt_file_path)
                if df_rpt is not None and not df_rpt.empty:
                    df_rpt['Value_Original_param_unit'] = df_rpt['Value_Original'] * MPA_TO_MMHG
                    slope = params_pcoup['slope']
                    intercept = params_pcoup['intercept']
                    df_rpt['Value_Corrected_param_unit'] = slope * df_rpt['Value_Original_param_unit'] + intercept
                    df_rpt['Value_Corrected_rpt_unit'] = df_rpt['Value_Corrected_param_unit'] * MMHG_TO_MPA
                    base, ext = os.path.splitext(PCOUP_RPT_FILE)
                    output_rpt_name = f"{base}_fixed{ext}"
                    output_rpt_path = os.path.join(sim_dir_path, output_rpt_name)
                    try:
                        df_to_save = df_rpt[['Time', 'Value_Corrected_rpt_unit']].copy()
                        df_to_save.columns = ['Time', 'Corrected_Value_MPa']
                        df_to_save.to_csv(output_rpt_path, sep=' ', header=False, index=False, float_format='%.6e')
                        print(f"    Archivo corregido guardado en: {output_rpt_name}")
                        total_files_corrected += 1
                    except Exception as e_save:
                        print(f"    ERROR al guardar archivo corregido '{output_rpt_name}': {e_save}")
                else:
                    print(f"    ADVERTENCIA: No se pudieron leer datos de {PCOUP_RPT_FILE}. Omitiendo corrección.")
            else:
                print(f"    INFO: Archivo {PCOUP_RPT_FILE} no encontrado en {sim_dir_name}. Omitiendo.")
        elif not PCOUP_RPT_FILE:
             print(f"  INFO: No se ha especificado PCOUP_RPT_FILE. Omitiendo corrección de presión coup.")
        else:
            print(f"  ADVERTENCIA: No hay parámetros de corrección para Presión Coup. Se omitirá {PCOUP_RPT_FILE}.")

        # --- Procesar archivo de Presión Contrecoup ---
        if params_pcontrecoup and PCONTRECOUP_RPT_FILE:
            rpt_file_path = os.path.join(sim_dir_path, PCONTRECOUP_RPT_FILE)
            if os.path.exists(rpt_file_path):
                total_files_processed_pressure += 1
                print(f"  Procesando archivo de Presión Contrecoup: {PCONTRECOUP_RPT_FILE}")
                df_rpt = read_rpt_file_for_correction(rpt_file_path)
                if df_rpt is not None and not df_rpt.empty:
                    df_rpt['Value_Original_param_unit'] = df_rpt['Value_Original'] * MPA_TO_MMHG
                    slope = params_pcontrecoup['slope']
                    intercept = params_pcontrecoup['intercept']
                    df_rpt['Value_Corrected_param_unit'] = slope * df_rpt['Value_Original_param_unit'] + intercept
                    df_rpt['Value_Corrected_rpt_unit'] = df_rpt['Value_Corrected_param_unit'] * MMHG_TO_MPA
                    base, ext = os.path.splitext(PCONTRECOUP_RPT_FILE)
                    output_rpt_name = f"{base}_fixed{ext}"
                    output_rpt_path = os.path.join(sim_dir_path, output_rpt_name)
                    try:
                        df_to_save = df_rpt[['Time', 'Value_Corrected_rpt_unit']].copy()
                        df_to_save.columns = ['Time', 'Corrected_Value_MPa']
                        df_to_save.to_csv(output_rpt_path, sep=' ', header=False, index=False, float_format='%.6e')
                        print(f"    Archivo corregido guardado en: {output_rpt_name}")
                        total_files_corrected +=1
                    except Exception as e_save:
                        print(f"    ERROR al guardar archivo corregido '{output_rpt_name}': {e_save}")
                else:
                    print(f"    ADVERTENCIA: No se pudieron leer datos de {PCONTRECOUP_RPT_FILE}. Omitiendo corrección.")
            else:
                print(f"    INFO: Archivo {PCONTRECOUP_RPT_FILE} no encontrado en {sim_dir_name}. Omitiendo.")
        elif not PCONTRECOUP_RPT_FILE:
            print(f"  INFO: No se ha especificado PCONTRECOUP_RPT_FILE. Omitiendo corrección de presión contrecoup.")
        else:
             print(f"  ADVERTENCIA: No hay parámetros de corrección para Presión Contrecoup. Se omitirá {PCONTRECOUP_RPT_FILE}.")

    print(f"\n--- Resumen de Corrección de Archivos .RPT ---")
    print(f"Simulaciones donde se intentó calcular y corregir magnitud de aceleración: {total_files_processed_accel_mag}")
    print(f"Archivos de presión (coup/contrecoup) intentados procesar: {total_files_processed_pressure}")
    print(f"Total de archivos .rpt corregidos y guardados (incluye magnitud de aceleración y presiones): {total_files_corrected}")
# --- FIN DE NUEVAS FUNCIONES ---


# --- Flujo Principal ---
if __name__ == "__main__":
    print("--- Iniciando Proceso de Análisis, Corrección y Aplicación a .RPT ---")
    # Montar Google Drive si se está en Colab
    try:
        from google.colab import drive
        drive.mount('/content/drive', force_remount=True)
        print("Google Drive montado correctamente.")
    except ImportError:
        print("No se está ejecutando en Google Colab o 'google.colab' no está disponible. Se asumirá que los archivos están localmente.")
        pass

    # FASES 1, 2 y 3: DERIVACIÓN DE PARÁMETROS Y VALIDACIÓN EN DATOS RESUMIDOS
    df_data = load_and_preprocess_data()

    params_accel = None
    params_pcoup = None
    params_pcontrecoup = None

    if df_data is not None and not df_data.empty:
        print("\n\n=== FASE 1: ANÁLISIS DEL ERROR SISTEMÁTICO (SOBRE DATOS RESUMIDOS) ===")
        valid_accel_data = plot_scatter_comparison(df_data, 'Acc_Sim_m_s2', 'Acc_Nahum_m_s2',
                                 'Aceleración (Magnitud)', 'm/s²', 'aceleracion_magnitud')
        plot_ratio_vs_severity(df_data, 'Ratio_Acc', 'v_cabeza_m_s',
                               'Ratio Aceleración (Magnitud)', 'Acel.Mag.', 'Velocidad de Impacto Sim. (m/s)', 'aceleracion_magnitud')

        valid_pcoup_data = plot_scatter_comparison(df_data, 'PCoup_Sim_mmHg', 'PCoup_Nahum_mmHg',
                                  'Presión de Golpe (Coup)', 'mmHg', 'pcoup')
        plot_ratio_vs_severity(df_data, 'Ratio_PCoup', 'v_cabeza_m_s',
                               'Ratio Presión de Golpe', 'P.Coup', 'Velocidad de Impacto Sim. (m/s)', 'pcoup')

        df_data['PContrecoup_Nahum_mmHg_Abs'] = df_data['PContrecoup_Nahum_mmHg'].abs()
        df_data['PContrecoup_Sim_mmHg_Abs'] = df_data['PContrecoup_Sim_mmHg'].abs()
        valid_pcontrecoup_data_abs = plot_scatter_comparison(df_data, 'PContrecoup_Sim_mmHg_Abs', 'PContrecoup_Nahum_mmHg_Abs',
                                      '|Presión de Contragolpe|', 'mmHg', 'pcontrecoup_abs')
        plot_ratio_vs_severity(df_data, 'Ratio_PContrecoup', 'v_cabeza_m_s',
                               'Ratio |Presión de Contragolpe|', '|P.Contrecoup|', 'Velocidad de Impacto Sim. (m/s)', 'pcontrecoup_abs')

        valid_tpico_data = plot_scatter_comparison(df_data, 'T_pico_Sim_ms', 'T_pico_Nahum_ms',
                                 'Tiempo de Pico', 'ms', 'tpico')
        plot_ratio_vs_severity(df_data, 'Ratio_Tpico', 'v_cabeza_m_s',
                               'Ratio Tiempo de Pico', 'T.Pico', 'Velocidad de Impacto Sim. (m/s)', 'tpico')


        print("\n\n=== FASE 2: DESARROLLO DEL MODELO DE CORRECCIÓN (REGRESIÓN LINEAL SOBRE DATOS RESUMIDOS) ===")
        all_regression_params_list = []
        params_accel = linear_regression_correction(valid_accel_data, 'Acc_Sim_m_s2', 'Acc_Nahum_m_s2', 'Aceleración (Magnitud)')
        if params_accel: all_regression_params_list.append(params_accel)

        params_pcoup = linear_regression_correction(valid_pcoup_data, 'PCoup_Sim_mmHg', 'PCoup_Nahum_mmHg', 'Presión Coup')
        if params_pcoup: all_regression_params_list.append(params_pcoup)

        valid_pcontrecoup_data_signed = df_data[['PContrecoup_Sim_mmHg', 'PContrecoup_Nahum_mmHg']].dropna()
        params_pcontrecoup = linear_regression_correction(valid_pcontrecoup_data_signed, 'PContrecoup_Sim_mmHg', 'PContrecoup_Nahum_mmHg', 'Presión Contrecoup (con signo)')
        if params_pcontrecoup: all_regression_params_list.append(params_pcontrecoup)

        params_tpico = linear_regression_correction(valid_tpico_data, 'T_pico_Sim_ms', 'T_pico_Nahum_ms', 'Tiempo de Pico')
        if params_tpico: all_regression_params_list.append(params_tpico)

        if all_regression_params_list:
            df_regression_summary = pd.DataFrame(all_regression_params_list)
            regression_txt_path = os.path.join(RESULTS_FOLDER, 'resumen_parametros_regresion.txt')
            regression_csv_path = os.path.join(RESULTS_FOLDER, 'resumen_parametros_regresion.csv')
            df_regression_summary.to_csv(regression_csv_path, index=False, sep=';', decimal=',')
            with open(regression_txt_path, 'w') as f:
                f.write("Resumen de Parámetros de Regresión Lineal (basado en datos resumidos):\n\n")
                f.write(df_regression_summary.to_string(index=False))
            print(f"\nResumen de parámetros de regresión (para datos resumidos) guardado en: {regression_txt_path} y {regression_csv_path}")

        print("\n\n=== FASE 3: APLICACIÓN Y VALIDACIÓN DE LA CORRECCIÓN (SOBRE DATOS RESUMIDOS) ===")
        df_data = apply_correction(df_data, 'Acc_Sim_m_s2', params_accel, 'Acc_Sim_Corregida')
        df_data = apply_correction(df_data, 'PCoup_Sim_mmHg', params_pcoup, 'PCoup_Sim_Corregida')
        df_data = apply_correction(df_data, 'PContrecoup_Sim_mmHg', params_pcontrecoup, 'PContrecoup_Sim_Corregida')
        df_data = apply_correction(df_data, 'T_pico_Sim_ms', params_tpico, 'T_pico_Sim_Corregida')

        # ... (resto de Fase 3 sin cambios) ...
        cols_summary = ['N_Ensayo',
                        'Acc_Nahum_m_s2', 'Acc_Sim_m_s2', 'Acc_Sim_Corregida',
                        'PCoup_Nahum_mmHg', 'PCoup_Sim_mmHg', 'PCoup_Sim_Corregida',
                        'PContrecoup_Nahum_mmHg', 'PContrecoup_Sim_mmHg', 'PContrecoup_Sim_Corregida',
                        'T_pico_Nahum_ms', 'T_pico_Sim_ms', 'T_pico_Sim_Corregida']
        df_summary_table = df_data[cols_summary].round(2)

        print("\n--- Tabla de Datos Resumidos con Correcciones Aplicadas ---")
        print(df_summary_table)
        summary_txt_path = os.path.join(RESULTS_FOLDER, 'tabla_datos_corregidos_resumen.txt')
        summary_csv_path = os.path.join(RESULTS_FOLDER, 'tabla_datos_corregidos_resumen.csv')
        df_summary_table.to_csv(summary_csv_path, index=False, sep=';', decimal=',')
        with open(summary_txt_path, 'w') as f:
            f.write("Tabla de Datos Resumidos con Correcciones Aplicadas:\n\n")
            f.write(df_summary_table.to_string(index=False))
        print(f"Tabla resumen de datos corregidos (resumidos) guardada en: {summary_txt_path} y {summary_csv_path}")

        plot_corrected_scatter(df_data, 'Acc_Sim_Corregida', 'Acc_Nahum_m_s2',
                               'Aceleración (Magnitud Resumida)', 'm/s²', 'aceleracion_magnitud')
        plot_corrected_scatter(df_data, 'PCoup_Sim_Corregida', 'PCoup_Nahum_mmHg',
                               'Presión de Golpe (Resumida)', 'mmHg', 'pcoup')
        plot_corrected_scatter(df_data, 'PContrecoup_Sim_Corregida', 'PContrecoup_Nahum_mmHg',
                               'Presión de Contragolpe (Resumida)', 'mmHg', 'pcontrecoup')
        plot_corrected_scatter(df_data, 'T_pico_Sim_Corregida', 'T_pico_Nahum_ms',
                               'Tiempo de Pico (Resumido)', 'ms', 'tpico')

        print("\n--- Evaluación Cuantitativa de la Corrección (MAPE sobre datos resumidos) ---")
        mape_results = []
        mape_acc_antes = calculate_mape(df_data['Acc_Nahum_m_s2'], df_data['Acc_Sim_m_s2'])
        mape_acc_despues = calculate_mape(df_data['Acc_Nahum_m_s2'], df_data['Acc_Sim_Corregida'])
        mape_results.append({'Métrica': 'Aceleración (Magnitud)', 'MAPE Antes (%)': mape_acc_antes, 'MAPE Después (%)': mape_acc_despues})

        mape_pcoup_antes = calculate_mape(df_data['PCoup_Nahum_mmHg'], df_data['PCoup_Sim_mmHg'])
        mape_pcoup_despues = calculate_mape(df_data['PCoup_Nahum_mmHg'], df_data['PCoup_Sim_Corregida'])
        mape_results.append({'Métrica': 'P. Coup', 'MAPE Antes (%)': mape_pcoup_antes, 'MAPE Después (%)': mape_pcoup_despues})

        mape_pcontrecoup_antes_abs = calculate_mape(df_data['PContrecoup_Nahum_mmHg'].abs(), df_data['PContrecoup_Sim_mmHg'].abs())
        mape_pcontrecoup_despues_abs = calculate_mape(df_data['PContrecoup_Nahum_mmHg'].abs(), df_data['PContrecoup_Sim_Corregida'].abs())
        mape_results.append({'Métrica': '|P. Contrecoup|', 'MAPE Antes (%)': mape_pcontrecoup_antes_abs, 'MAPE Después (%)': mape_pcontrecoup_despues_abs})

        mape_tpico_antes = calculate_mape(df_data['T_pico_Sim_ms'], df_data['T_pico_Sim_ms'])
        mape_tpico_despues = calculate_mape(df_data['T_pico_Nahum_ms'], df_data['T_pico_Sim_Corregida'])
        mape_results.append({'Métrica': 'T. Pico', 'MAPE Antes (%)': mape_tpico_antes, 'MAPE Después (%)': mape_tpico_despues})

        df_mape_summary = pd.DataFrame(mape_results)
        print(df_mape_summary.round(2))
        mape_txt_path = os.path.join(RESULTS_FOLDER, 'resumen_mape.txt')
        mape_csv_path = os.path.join(RESULTS_FOLDER, 'resumen_mape.csv')
        df_mape_summary.to_csv(mape_csv_path, index=False, sep=';', decimal=',')
        with open(mape_txt_path, 'w') as f:
            f.write("Resumen de Evaluación MAPE (sobre datos resumidos):\n\n")
            f.write(df_mape_summary.to_string(index=False))
        print(f"Resumen MAPE (datos resumidos) guardado en: {mape_txt_path} y {mape_csv_path}")

        full_data_csv_path = os.path.join(RESULTS_FOLDER, 'datos_completos_analizados_resumidos.csv')
        df_data.to_csv(full_data_csv_path, index=False, sep=';', decimal=',')
        print(f"\nDataFrame completo con todos los cálculos (datos resumidos) guardado en: {full_data_csv_path}")

        print("\n--- Análisis de Datos Resumidos Completado ---")
        print(f"Resultados del análisis de datos resumidos guardados en: '{RESULTS_FOLDER}'")

    else:
        print("Error: No se pudieron cargar o preprocesar los datos resumidos. El análisis de datos resumidos y la corrección de .RPT se detuvieron.")
        params_accel, params_pcoup, params_pcontrecoup = None, None, None

    # FASE 4: APLICACIÓN DE CORRECCIÓN A ARCHIVOS .RPT
    if params_accel or params_pcoup or params_pcontrecoup:
        process_simulation_rpts_in_directory_structure(
            REPORTS_ROOT_DIR_FOR_CORRECTION,
            params_accel,
            params_pcoup,
            params_pcontrecoup
        )
    else:
        print("\nADVERTENCIA: No se obtuvieron parámetros de corrección de las fases anteriores (datos resumidos).")
        print("No se procederá con la corrección de archivos .RPT.")

    print("\n--- Proceso General Completado ---")
