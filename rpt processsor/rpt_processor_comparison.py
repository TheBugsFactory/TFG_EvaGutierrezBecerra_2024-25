import os
import re
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import traceback
import string
from typing import List, Dict, Tuple, Optional, Any

# --- Configuración General ---
REPORTS_ROOT_DIR = '/content/drive/MyDrive/Beca Colaboracion 2024-2025/10_Resultados Simulaciones/Reports_v3'
RESULTS_COMPARISON_DIR = '/content/drive/MyDrive/Beca Colaboracion 2024-2025/10_Resultados Simulaciones/Results_Comparison_v3'

# --- Configuración de Identificación de Simulaciones y Archivos ---
NO_HELMET_KEYWORDS = ['nohelmet', 'sincasco', 'nahum']
HELMET_KEYWORDS = ['helmet', 'concasco', 'base']

ACCEL_COMPONENTS_RPT_NAMES = {
    'A1': 'A1_Acc_mean.rpt',
    'A2': 'A2_Acc_mean.rpt',
    'A3': 'A3_Acc_mean.rpt'
}
PRESSURE_TOP_RPT_SUFFIX = "_Pressure_TOPREF_mean.rpt"
PRESSURE_BOTTOM_RPT_SUFFIX = "_Pressure_BOTTOMREF_mean.rpt"

TIME_COLUMN_INDEX = 0
VALUE_COLUMN_INDEX = 1
RPT_IGNORE_LINE_PATTERNS = [r'^\s*\*+', r'^\s*END STEP', r'^\s*THE ANALYSIS', r'^\s*FIELD OUTPUT']

sns.set_theme(style="whitegrid", palette="deep")
COMPARISON_PALETTE = sns.color_palette("deep", n_colors=4)

# --- NUEVA FUNCIÓN PARA EXTRAER INFORMACIÓN PARA TÍTULOS ---
def extract_title_info(sim_name: str) -> Tuple[str, float, str]:
    """
    Extrae el estado del casco y la velocidad del nombre de la simulación.
    Ejemplo: "6mayo_ConCasco_Ramiro_v3740" -> ("con casco", 3.74, "ConCasco_v3740")
             "6mayo_SinCasco_Ramiro_v4340" -> ("sin casco", 4.34, "SinCasco_v4340")

    Devuelve:
        (str): Descripción del casco ("con casco", "sin casco", "desconocido").
        (float): Velocidad en m/s. None si no se encuentra.
        (str): Fragmento del nombre para identificar (ej: "ConCasco_v3740")
    """
    sim_name_lower = sim_name.lower()
    helmet_status_str = "tipo desconocido"
    short_id_parts = []

    if any(keyword in sim_name_lower for keyword in HELMET_KEYWORDS):
        helmet_status_str = "con casco"
        # Trata de encontrar la keyword original para el short_id
        for kw in HELMET_KEYWORDS:
            if kw in sim_name_lower:
                # Intentar encontrar la version original case-sensitive
                match_kw = re.search(f'({kw})', sim_name, re.IGNORECASE)
                if match_kw:
                    short_id_parts.append(match_kw.group(1))
                    break
        if not any(kw in short_id_parts for kw in HELMET_KEYWORDS): # Fallback si no encuentra original
             short_id_parts.append("ConCasco")


    elif any(keyword in sim_name_lower for keyword in NO_HELMET_KEYWORDS):
        helmet_status_str = "sin casco"
        for kw in NO_HELMET_KEYWORDS:
            if kw in sim_name_lower:
                match_kw = re.search(f'({kw})', sim_name, re.IGNORECASE)
                if match_kw:
                    short_id_parts.append(match_kw.group(1))
                    break
        if not any(kw in short_id_parts for kw in NO_HELMET_KEYWORDS):
             short_id_parts.append("SinCasco")

    velocity_m_s = None
    velocity_mm_s_str = None
    # Buscar patrón como _v3740, v3740, _V3740, V3740
    match_vel = re.search(r'_?[vV](\d+)', sim_name)
    if match_vel:
        velocity_mm_s_str = match_vel.group(0) # ej: _v3740
        short_id_parts.append(velocity_mm_s_str.replace("_","")) # ej: v3740
        velocity_mm_s = int(match_vel.group(1))
        velocity_m_s = velocity_mm_s / 1000.0

    short_id = "_".join(filter(None, short_id_parts))
    if not short_id: # Fallback si no se pudo construir un ID corto
        # Tomar los primeros N caracteres o alguna parte distintiva
        parts = sim_name.split('_')
        if len(parts) > 1:
            short_id = f"{parts[1]}_{parts[-1]}" # ej ConCasco_v3740 de 6mayo_ConCasco_Ramiro_v3740
        else:
            short_id = sim_name[:15] # Truncar si es un nombre muy largo sin underscores

    return helmet_status_str, velocity_m_s, short_id


# --- Funciones Auxiliares (sin cambios, pero necesarias) ---
def find_rpt_file_flexible(directory: str, primary_suffix: str, secondary_name: Optional[str] = None) -> Optional[str]:
    sim_name = os.path.basename(directory)
    expected_filename_option1 = sim_name + primary_suffix
    if os.path.exists(os.path.join(directory, expected_filename_option1)):
        return os.path.join(directory, expected_filename_option1)
    if secondary_name:
        if os.path.exists(os.path.join(directory, secondary_name)):
            return os.path.join(directory, secondary_name)
    elif primary_suffix.startswith("_"):
        fallback_name = primary_suffix[1:]
        if os.path.exists(os.path.join(directory, fallback_name)):
            return os.path.join(directory, fallback_name)
    try:
        for fname in os.listdir(directory):
            if fname.endswith(primary_suffix):
                return os.path.join(directory, fname)
    except FileNotFoundError:
        pass
    return None

def read_rpt_data(file_path: str) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    if not file_path or not os.path.exists(file_path):
        print(f"      ERROR: Archivo RPT no encontrado o no accesible: {file_path}")
        return None
    time_data, value_data = [], []
    data_lines_found = 0
    try:
        with open(file_path, 'r') as f:
            for line_num, line_content in enumerate(f):
                line = line_content.strip()
                if not line: continue
                is_ignorable = False
                for pattern in RPT_IGNORE_LINE_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        is_ignorable = True
                        break
                if is_ignorable: continue
                try:
                    parts = re.split(r'\s+', line)
                    if len(parts) > max(TIME_COLUMN_INDEX, VALUE_COLUMN_INDEX):
                        time = float(parts[TIME_COLUMN_INDEX])
                        value = float(parts[VALUE_COLUMN_INDEX])
                        time_data.append(time)
                        value_data.append(value)
                        data_lines_found += 1
                except ValueError:
                    continue
        if not time_data or not value_data:
            # print(f"      WARNING: No se extrajeron datos numéricos de {file_path} (líneas leídas: {data_lines_found}).") # Comentado para reducir verbosidad
            return None
        return np.array(time_data) * 1000, np.array(value_data)
    except Exception as e:
        print(f"      ERROR: Fallo al leer o procesar {file_path}: {e}")
        traceback.print_exc()
        return None

def calculate_acceleration_magnitude(dir_path: str, sim_name: str) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    print(f"  Calculando magnitud de aceleración desde componentes para {sim_name}...")
    components_values: Dict[str, np.ndarray] = {}
    common_time: Optional[np.ndarray] = None
    min_len = float('inf')
    conversion_factor_accel = 1.0 / 1000.0  # mm/s^2 a m/s^2

    for comp_key, rpt_pattern_or_name in ACCEL_COMPONENTS_RPT_NAMES.items():
        component_rpt = find_rpt_file_flexible(dir_path, rpt_pattern_or_name, rpt_pattern_or_name)
        if component_rpt:
            data = read_rpt_data(component_rpt)
            if data:
                current_time_ms, current_values_mm_s2 = data
                current_values_m_s2 = current_values_mm_s2 * conversion_factor_accel
                components_values[comp_key] = current_values_m_s2
                if common_time is None:
                    common_time = current_time_ms
                    min_len = len(common_time)
                else:
                    if len(current_time_ms) != len(common_time) or not np.allclose(common_time[:min(len(common_time), len(current_time_ms))], current_time_ms[:min(len(common_time), len(current_time_ms))]):
                        new_min_len = min(len(common_time), len(current_time_ms))
                        if new_min_len < min_len: min_len = new_min_len
                        print(f"      WARNING: Tiempos de componentes de aceleración no idénticos para {sim_name}. Se truncará a {min_len} puntos.")
                min_len = min(min_len, len(current_values_m_s2))
            else:
                print(f"      ERROR: No se pudieron leer datos para componente {comp_key} de {sim_name} desde {component_rpt}")
                return None
        else:
            print(f"      ERROR: No se encontró RPT para componente {comp_key} ('{rpt_pattern_or_name}') en {dir_path}")
            return None

    if len(components_values) != 3 or common_time is None:
        print(f"      ERROR: No se encontraron todas las componentes de aceleración para {sim_name}.")
        return None

    common_time = common_time[:min_len]
    a1 = components_values['A1'][:min_len]
    a2 = components_values['A2'][:min_len]
    a3 = components_values['A3'][:min_len]

    if not (len(a1) == min_len and len(a2) == min_len and len(a3) == min_len):
        print(f"      ERROR: Discrepancia en longitudes de componentes de aceleración para {sim_name} tras truncado.")
        return None

    magnitude_m_s2 = np.sqrt(a1**2 + a2**2 + a3**2)
    # print(f"  Magnitud de aceleración calculada (m/s²) para {sim_name} (longitud: {len(magnitude_m_s2)}). Tiempo en ms.") # Comentado
    return common_time, magnitude_m_s2

def get_simulation_data(dir_path: str) -> Optional[Dict[str, Any]]:
    sim_name = os.path.basename(dir_path)
    print(f"\nProcesando simulación: {sim_name}")
    accel_data = calculate_acceleration_magnitude(dir_path, sim_name)
    if not accel_data: return None
    time_acc_ms, acc_mag_m_s2 = accel_data
    pressure_top_rpt = find_rpt_file_flexible(dir_path, PRESSURE_TOP_RPT_SUFFIX, PRESSURE_TOP_RPT_SUFFIX[1:] if PRESSURE_TOP_RPT_SUFFIX.startswith('_') else PRESSURE_TOP_RPT_SUFFIX)
    pressure_top_data = read_rpt_data(pressure_top_rpt) if pressure_top_rpt else None
    # if not pressure_top_data: print(f"  Advertencia: No datos de Presión Top para {sim_name} (buscado: {os.path.basename(pressure_top_rpt if pressure_top_rpt else 'N/A')}).") # Comentado
    pressure_bottom_rpt = find_rpt_file_flexible(dir_path, PRESSURE_BOTTOM_RPT_SUFFIX, PRESSURE_BOTTOM_RPT_SUFFIX[1:] if PRESSURE_BOTTOM_RPT_SUFFIX.startswith('_') else PRESSURE_BOTTOM_RPT_SUFFIX)
    pressure_bottom_data = read_rpt_data(pressure_bottom_rpt) if pressure_bottom_rpt else None
    # if not pressure_bottom_data: print(f"  Advertencia: No datos de Presión Bottom para {sim_name} (buscado: {os.path.basename(pressure_bottom_rpt if pressure_bottom_rpt else 'N/A')}).") # Comentado

    return {
        'name': sim_name, 'dir_path': dir_path,
        'time_acc_ms': time_acc_ms, 'acc_mag_m_s2': acc_mag_m_s2,
        'time_p_top_ms': pressure_top_data[0] if pressure_top_data else None,
        'pressure_top_mpa': pressure_top_data[1] if pressure_top_data else None,
        'time_p_bottom_ms': pressure_bottom_data[0] if pressure_bottom_data else None,
        'pressure_bottom_mpa': pressure_bottom_data[1] if pressure_bottom_data else None,
    }

# --- Funciones de Graficación (MODIFICADAS) ---

def plot_individual_pressures(sim_data: Dict[str, Any], results_dir: str):
    name = sim_data['name']
    helmet_status, velocity_m_s, short_id = extract_title_info(name)

    title_vel_part = f"a {velocity_m_s:.2f} m/s" if velocity_m_s is not None else "(velocidad desconocida)"
    main_title = f"Impacto {helmet_status} {title_vel_part}\nPresión Intracraneal (Top y Bottom)"

    fig, ax = plt.subplots(figsize=(12, 6))
    plt.title(main_title, fontsize=16, fontweight='bold')

    time_unit_label = 'Tiempo (ms)'
    pressure_unit_label = 'Presión (MPa)'
    lines_for_legend = []
    if sim_data['time_p_top_ms'] is not None and sim_data['pressure_top_mpa'] is not None:
        line_ptop, = ax.plot(sim_data['time_p_top_ms'], sim_data['pressure_top_mpa'], color=COMPARISON_PALETTE[1], linestyle='--', linewidth=2, label=f'Presión Top ({pressure_unit_label})')
        lines_for_legend.append(line_ptop)
    if sim_data['time_p_bottom_ms'] is not None and sim_data['pressure_bottom_mpa'] is not None:
        line_pbottom, = ax.plot(sim_data['time_p_bottom_ms'], sim_data['pressure_bottom_mpa'], color=COMPARISON_PALETTE[2], linestyle=':', linewidth=2, label=f'Presión Bottom ({pressure_unit_label})')
        lines_for_legend.append(line_pbottom)

    ax.set_xlabel(time_unit_label, fontsize=12)
    ax.set_ylabel(pressure_unit_label, fontsize=12)
    ax.grid(True, which='major', linestyle=':', linewidth=0.5, color='grey', alpha=0.7)
    if lines_for_legend:
        labels = [l.get_label() for l in lines_for_legend]
        ax.legend(lines_for_legend, labels, loc='upper right', fontsize=10, frameon=True, facecolor='white', framealpha=0.7)
    else:
        ax.text(0.5, 0.5, "No hay datos de presión disponibles.", horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)

    fig.tight_layout()
    filename_safe_short_id = re.sub(r'[^\w\-_\.]', '_', short_id) # Sanitize for filename
    plt.savefig(os.path.join(results_dir, f"Individual_Pressures_{filename_safe_short_id}.png"))
    plt.close(fig)


def plot_individual_accel_and_pressures(sim_data: Dict[str, Any], results_dir: str):
    name = sim_data['name']
    helmet_status, velocity_m_s, short_id = extract_title_info(name)

    title_vel_part = f"a {velocity_m_s:.2f} m/s" if velocity_m_s is not None else "(velocidad desconocida)"
    main_title = f"Impacto {helmet_status} {title_vel_part}\nAceleración y Presión Intracraneal"

    fig, ax1 = plt.subplots(figsize=(14, 7))
    plt.title(main_title, fontsize=16, fontweight='bold')

    time_unit_label = 'Tiempo (ms)'
    acc_unit_label = 'm/s²'
    pressure_unit_label = 'MPa'

    color_acc = COMPARISON_PALETTE[0]
    ax1.set_xlabel(time_unit_label, fontsize=12)
    ax1.set_ylabel(f'Aceleración Magnitud ({acc_unit_label})', color=color_acc, fontsize=12)
    line_acc, = ax1.plot(sim_data['time_acc_ms'], sim_data['acc_mag_m_s2'], color=color_acc, linestyle='-', linewidth=2, label=f'Aceleración Mag. ({acc_unit_label})')
    ax1.tick_params(axis='y', labelcolor=color_acc)
    ax1.grid(True, which='major', axis='y', linestyle=':', linewidth=0.5, color=color_acc, alpha=0.5)

    ax2 = ax1.twinx()
    color_p_top = COMPARISON_PALETTE[1]
    color_p_bottom = COMPARISON_PALETTE[2]
    ax2.set_ylabel(f'Presión ({pressure_unit_label})', fontsize=12)

    lines_for_legend = [line_acc]
    if sim_data['time_p_top_ms'] is not None and sim_data['pressure_top_mpa'] is not None:
        line_ptop, = ax2.plot(sim_data['time_p_top_ms'], sim_data['pressure_top_mpa'], color=color_p_top, linestyle='--', linewidth=2, label=f'Presión Top ({pressure_unit_label})')
        lines_for_legend.append(line_ptop)
    if sim_data['time_p_bottom_ms'] is not None and sim_data['pressure_bottom_mpa'] is not None:
        line_pbottom, = ax2.plot(sim_data['time_p_bottom_ms'], sim_data['pressure_bottom_mpa'], color=color_p_bottom, linestyle=':', linewidth=2, label=f'Presión Bottom ({pressure_unit_label})')
        lines_for_legend.append(line_pbottom)

    ax2.tick_params(axis='y')
    ax1.grid(True, which='major', axis='x', linestyle='-', linewidth=0.5, color='lightgrey', alpha=0.7)
    labels = [l.get_label() for l in lines_for_legend]
    ax1.legend(lines_for_legend, labels, loc='upper right', fontsize=10, frameon=True, facecolor='white', framealpha=0.7)
    fig.tight_layout()
    filename_safe_short_id = re.sub(r'[^\w\-_\.]', '_', short_id) # Sanitize for filename
    plt.savefig(os.path.join(results_dir, f"Individual_AccAndPressures_{filename_safe_short_id}.png"))
    plt.close(fig)


def plot_comparison_acceleration(sim_nh_data: Dict[str, Any], sim_h_data: Dict[str, Any], results_dir: str):
    name_nh, time_nh_ms, acc_nh_m_s2 = sim_nh_data['name'], sim_nh_data['time_acc_ms'], sim_nh_data['acc_mag_m_s2']
    name_h, time_h_ms, acc_h_m_s2 = sim_h_data['name'], sim_h_data['time_acc_ms'], sim_h_data['acc_mag_m_s2']

    _, velocity_m_s_nh, short_id_nh = extract_title_info(name_nh)
    _, velocity_m_s_h, short_id_h = extract_title_info(name_h)

    final_velocity_m_s = velocity_m_s_nh if velocity_m_s_nh is not None else velocity_m_s_h
    title_vel_part = f"a {final_velocity_m_s:.2f} m/s" if final_velocity_m_s is not None else "(velocidad desconocida)"
    main_title = f"Gráfica comparativa de Impacto con casco y sin casco {title_vel_part}"

    fig, ax1 = plt.subplots(figsize=(14, 7))

    time_unit_label = 'Tiempo (ms)'
    acc_unit_label_left = 'Aceleración (m/s²)'
    acc_unit_label_right = 'Aceleración (mm/s²)'

    color_nh = COMPARISON_PALETTE[0]
    color_h = COMPARISON_PALETTE[1]

    # Eje izquierdo para Sin Casco (m/s²)
    ax1.set_xlabel(time_unit_label, fontsize=12)
    ax1.set_ylabel(acc_unit_label_left, color=color_nh, fontsize=12)
    line_nh, = ax1.plot(time_nh_ms, acc_nh_m_s2, label=f'Sin Casco ({short_id_nh}) - m/s²', color=color_nh, linewidth=2)
    ax1.tick_params(axis='y', labelcolor=color_nh)
    ax1.grid(True, which='major', axis='y', linestyle=':', linewidth=0.5, color=color_nh, alpha=0.5)
    # Aplicar notación científica al eje Y izquierdo
    ax1.ticklabel_format(style='sci', axis='y', scilimits=(0,0), useMathText=True)


    # Eje derecho para Con Casco (mm/s²)
    ax2 = ax1.twinx()
    acc_h_mm_s2 = acc_h_m_s2 * 1000
    ax2.set_ylabel(acc_unit_label_right, color=color_h, fontsize=12)
    line_h, = ax2.plot(time_h_ms, acc_h_mm_s2, label=f'Con Casco ({short_id_h}) - mm/s²', color=color_h, linewidth=2, linestyle='--')
    ax2.tick_params(axis='y', labelcolor=color_h)
    # Aplicar notación científica al eje Y derecho
    ax2.ticklabel_format(style='sci', axis='y', scilimits=(0,0), useMathText=True)


    ax1.grid(True, which='major', axis='x', linestyle='-', linewidth=0.5, color='lightgrey', alpha=0.7)
    plt.title(f"{main_title}\nComparación de Magnitud de Aceleración", fontsize=15, fontweight='bold')

    lines = [line_nh, line_h]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper right', fontsize=10, frameon=True)

    sns.despine(fig=fig, right=False)
    fig.tight_layout()

    filename_safe_short_id_nh = re.sub(r'[^\w\-_\.]', '_', short_id_nh)
    filename_safe_short_id_h = re.sub(r'[^\w\-_\.]', '_', short_id_h)
    plt.savefig(os.path.join(results_dir, f"Compare_AccMag_DualAxis_Sci_{filename_safe_short_id_nh}_vs_{filename_safe_short_id_h}.png"))
    plt.close(fig)

def plot_comparison_pressure(sim_nh_data: Dict[str, Any], sim_h_data: Dict[str, Any], results_dir: str):
    name_nh, name_h = sim_nh_data['name'], sim_h_data['name']

    _, velocity_m_s_nh, short_id_nh = extract_title_info(name_nh)
    _, velocity_m_s_h, short_id_h = extract_title_info(name_h)

    final_velocity_m_s = velocity_m_s_nh if velocity_m_s_nh is not None else velocity_m_s_h
    title_vel_part = f"a {final_velocity_m_s:.2f} m/s" if final_velocity_m_s is not None else "(velocidad desconocida)"
    super_title = f"Gráfica comparativa de Impacto con casco y sin casco {title_vel_part}\nComparación de Presión Intracraneal"

    fig, axs = plt.subplots(2, 1, figsize=(14, 12), sharex=True)

    time_unit_label = 'Tiempo (ms)'
    pressure_unit_nh_label = 'Presión (MPa)'
    pressure_unit_h_label = 'Presión (kPa)'

    color_nh = COMPARISON_PALETTE[0]
    color_h = COMPARISON_PALETTE[1]

    # --- Subplot para Presión Top (Coup) ---
    ax_top_nh = axs[0]
    ax_top_h = ax_top_nh.twinx()
    lines_top, labels_top = [], []

    if sim_nh_data['time_p_top_ms'] is not None and sim_nh_data['pressure_top_mpa'] is not None:
        line_nh_top, = ax_top_nh.plot(sim_nh_data['time_p_top_ms'], sim_nh_data['pressure_top_mpa'],
                                  label=f'Sin Casco ({short_id_nh}) - MPa', color=color_nh, linewidth=2)
        lines_top.append(line_nh_top); labels_top.append(f'Sin Casco ({short_id_nh}) - MPa')
    ax_top_nh.set_ylabel(f'{pressure_unit_nh_label} (Sin Casco)', color=color_nh, fontsize=12)
    ax_top_nh.tick_params(axis='y', labelcolor=color_nh)
    ax_top_nh.grid(True, which='major', axis='y', linestyle=':', linewidth=0.5, color=color_nh, alpha=0.5)

    if sim_h_data['time_p_top_ms'] is not None and sim_h_data['pressure_top_mpa'] is not None:
        pressure_h_kpa = sim_h_data['pressure_top_mpa'] * 1000
        line_h_top, = ax_top_h.plot(sim_h_data['time_p_top_ms'], pressure_h_kpa,
                                label=f'Con Casco ({short_id_h}) - kPa', color=color_h, linewidth=2, linestyle='--')
        lines_top.append(line_h_top); labels_top.append(f'Con Casco ({short_id_h}) - kPa')
    ax_top_h.set_ylabel(f'{pressure_unit_h_label} (Con Casco)', color=color_h, fontsize=12)
    ax_top_h.tick_params(axis='y', labelcolor=color_h)

    axs[0].set_title(f'Comparación de Presión en Top (Coup)', fontsize=14, fontweight='bold')
    if lines_top: axs[0].legend(lines_top, labels_top, loc='upper right', fontsize=9)

    # --- Subplot para Presión Bottom (Contrecoup) ---
    ax_bottom_nh = axs[1]
    ax_bottom_h = ax_bottom_nh.twinx()
    lines_bottom, labels_bottom = [], []

    if sim_nh_data['time_p_bottom_ms'] is not None and sim_nh_data['pressure_bottom_mpa'] is not None:
        line_nh_b, = ax_bottom_nh.plot(sim_nh_data['time_p_bottom_ms'], sim_nh_data['pressure_bottom_mpa'],
                                       label=f'Sin Casco ({short_id_nh}) - MPa', color=color_nh, linewidth=2)
        lines_bottom.append(line_nh_b); labels_bottom.append(f'Sin Casco ({short_id_nh}) - MPa')
    ax_bottom_nh.set_ylabel(f'{pressure_unit_nh_label} (Sin Casco)', color=color_nh, fontsize=12)
    ax_bottom_nh.tick_params(axis='y', labelcolor=color_nh)
    ax_bottom_nh.grid(True, which='major', axis='y', linestyle=':', linewidth=0.5, color=color_nh, alpha=0.5)

    if sim_h_data['time_p_bottom_ms'] is not None and sim_h_data['pressure_bottom_mpa'] is not None:
        pressure_h_kpa_b = sim_h_data['pressure_bottom_mpa'] * 1000
        line_h_b, = ax_bottom_h.plot(sim_h_data['time_p_bottom_ms'], pressure_h_kpa_b,
                                     label=f'Con Casco ({short_id_h}) - kPa', color=color_h, linewidth=2, linestyle='--')
        lines_bottom.append(line_h_b); labels_bottom.append(f'Con Casco ({short_id_h}) - kPa')
    ax_bottom_h.set_ylabel(f'{pressure_unit_h_label} (Con Casco)', color=color_h, fontsize=12)
    ax_bottom_h.tick_params(axis='y', labelcolor=color_h)

    axs[1].set_title(f'Comparación de Presión en Bottom (Contrecoup)', fontsize=14, fontweight='bold')
    axs[1].set_xlabel(time_unit_label, fontsize=12)
    if lines_bottom: axs[1].legend(lines_bottom, labels_bottom, loc='upper right', fontsize=9)

    axs[0].grid(True, which='major', axis='x', linestyle='-', linewidth=0.5, color='lightgrey', alpha=0.7)
    axs[1].grid(True, which='major', axis='x', linestyle='-', linewidth=0.5, color='lightgrey', alpha=0.7)

    sns.despine(fig=fig, right=False)
    fig.subplots_adjust(right=0.85)
    plt.suptitle(super_title, fontsize=16, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 0.9, 0.95])

    filename_safe_short_id_nh = re.sub(r'[^\w\-_\.]', '_', short_id_nh)
    filename_safe_short_id_h = re.sub(r'[^\w\-_\.]', '_', short_id_h)
    plt.savefig(os.path.join(results_dir, f"Compare_Pressure_DualAxes_{filename_safe_short_id_nh}_vs_{filename_safe_short_id_h}.png"))
    plt.close(fig)

# --- Lógica Principal (sin cambios significativos, pero he limpiado algunos prints) ---
def main():
    global get_simulation_data, plot_individual_pressures, plot_individual_accel_and_pressures
    global plot_comparison_acceleration, plot_comparison_pressure

    if not os.path.exists(REPORTS_ROOT_DIR):
        print(f"ERROR: El directorio raíz de reportes '{REPORTS_ROOT_DIR}' no existe.")
        return
    if not os.path.exists(RESULTS_COMPARISON_DIR):
        os.makedirs(RESULTS_COMPARISON_DIR, exist_ok=True)
        print(f"Directorio de resultados creado: '{RESULTS_COMPARISON_DIR}'")

    all_sim_dirs = [d for d in os.listdir(REPORTS_ROOT_DIR) if os.path.isdir(os.path.join(REPORTS_ROOT_DIR, d))]
    no_helmet_sims, helmet_sims = [], []

    no_helmet_keywords_lower = [kw.lower() for kw in NO_HELMET_KEYWORDS]
    helmet_keywords_lower = [kw.lower() for kw in HELMET_KEYWORDS]

    for sim_dir_name in all_sim_dirs:
        dir_name_lower = sim_dir_name.lower()
        sim_full_path = os.path.join(REPORTS_ROOT_DIR, sim_dir_name)
        is_no_helmet = any(keyword in dir_name_lower for keyword in no_helmet_keywords_lower)
        is_helmet = any(keyword in dir_name_lower for keyword in helmet_keywords_lower)

        if is_no_helmet and not is_helmet:
            no_helmet_sims.append({'id': sim_dir_name, 'path': sim_full_path})
        elif is_helmet and not is_no_helmet:
            helmet_sims.append({'id': sim_dir_name, 'path': sim_full_path})
        elif is_helmet and is_no_helmet:
            print(f"Advertencia: Directorio '{sim_dir_name}' es ambiguo. Omitiendo.")
        # else:
            # print(f"Info: Directorio '{sim_dir_name}' no clasificado como con o sin casco. Omitiendo.")


    if not no_helmet_sims: print("No se encontraron simulaciones SIN CASCO."); return
    if not helmet_sims: print("No se encontraron simulaciones CON CASCO."); return

    letters = string.ascii_lowercase
    print("\n--- Simulaciones CON CASCO Encontradas (seleccionar por NÚMERO) ---")
    for i, sim in enumerate(helmet_sims): print(f"  {i+1}: {sim['id']}")
    print("\n--- Simulaciones SIN CASCO Encontradas (seleccionar por LETRA) ---")
    for i, sim in enumerate(no_helmet_sims):
        label = letters[i] if i < len(letters) else f"NH{i - len(letters) + 1}"
        print(f"  {label}: {sim['id']}")

    selected_pairs = []
    while True:
        try:
            user_input = input(
                "\nIntroduce pares para comparar (ej: 1a, 3b). 'fin' para terminar: "
            ).lower().strip()
            if user_input == 'fin': break
            if not user_input: continue
            pair_strings = re.split(r'[,\s]+', user_input)
            current_input_valid_pairs = []
            any_error_in_current_input = False
            for pair_str in pair_strings:
                if not pair_str: continue
                match = re.fullmatch(r'(\d+)([a-z])', pair_str)
                if match:
                    h_num_str, nh_letter_str = match.group(1), match.group(2)
                    idx_h, idx_nh = int(h_num_str) - 1, ord(nh_letter_str) - ord('a')
                    if 0 <= idx_h < len(helmet_sims) and 0 <= idx_nh < len(no_helmet_sims):
                        pair_to_add = (no_helmet_sims[idx_nh], helmet_sims[idx_h])
                        if pair_to_add not in selected_pairs and pair_to_add not in current_input_valid_pairs:
                            current_input_valid_pairs.append(pair_to_add)
                            print(f"  Par candidato: '{no_helmet_sims[idx_nh]['id']}' vs '{helmet_sims[idx_h]['id']}'")
                        else: print(f"  Advertencia: Par ya seleccionado o repetido. Omitiendo.")
                    else:
                        print(f"  Error: Selección '{pair_str}' fuera de rango.")
                        any_error_in_current_input = True
                else:
                    print(f"  Error: Formato inválido '{pair_str}'.")
                    any_error_in_current_input = True
            if not any_error_in_current_input and current_input_valid_pairs:
                selected_pairs.extend(current_input_valid_pairs)
                print(f"Pares añadidos. Total: {len(selected_pairs)}")
        except ValueError: print("Entrada no válida.")
        except Exception as e: print(f"Error inesperado: {e}")

    if not selected_pairs: print("No se seleccionaron pares. Saliendo."); return

    print(f"\n--- Procesando {len(selected_pairs)} Pares Seleccionados ---")
    for i, (sim_nh_info, sim_h_info) in enumerate(selected_pairs):
        print(f"\n--- Par {i+1}/{len(selected_pairs)}: '{sim_nh_info['id']}' vs. '{sim_h_info['id']}' ---")
        data_nh = get_simulation_data(sim_nh_info['path'])
        data_h = get_simulation_data(sim_h_info['path'])
        if not data_nh or not data_h:
            print(f"  ERROR: Faltan datos. Omitiendo par."); continue

        print(f"  Generando gráficas individuales para '{data_nh['name']}'...")
        plot_individual_pressures(data_nh, RESULTS_COMPARISON_DIR)
        plot_individual_accel_and_pressures(data_nh, RESULTS_COMPARISON_DIR)
        print(f"  Generando gráficas individuales para '{data_h['name']}'...")
        plot_individual_pressures(data_h, RESULTS_COMPARISON_DIR)
        plot_individual_accel_and_pressures(data_h, RESULTS_COMPARISON_DIR)

        if data_nh.get('acc_mag_m_s2') is not None and data_h.get('acc_mag_m_s2') is not None:
            print(f"  Generando gráfica comparativa de aceleración...")
            plot_comparison_acceleration(data_nh, data_h, RESULTS_COMPARISON_DIR)
        # else: print("  Advertencia: Faltan datos de aceleración. Omitiendo gráfica comparativa de aceleración.") # Comentado

        can_plot_pressure_nh = data_nh.get('pressure_top_mpa') is not None or data_nh.get('pressure_bottom_mpa') is not None
        can_plot_pressure_h = data_h.get('pressure_top_mpa') is not None or data_h.get('pressure_bottom_mpa') is not None
        if can_plot_pressure_nh or can_plot_pressure_h:
            print(f"  Generando gráfica comparativa de presión...")
            plot_comparison_pressure(data_nh, data_h, RESULTS_COMPARISON_DIR)
        # else: print("  Advertencia: No hay datos de presión. Omitiendo gráfica comparativa de presión.") # Comentado

    print(f"\n--- Proceso Completado. Resultados guardados en: '{RESULTS_COMPARISON_DIR}' ---")

if __name__ == '__main__':
    main()
