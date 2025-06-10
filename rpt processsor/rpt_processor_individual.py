import os
import re
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import traceback
import string
from typing import List, Dict, Tuple, Optional, Any

# --- Configuración General ---
REPORTS_ROOT_DIR = '/content/drive/MyDrive/Beca Colaboracion 2024-2025/10_Resultados Simulaciones/Reports_Nahum_v3'
RESULTS_COMPARISON_DIR_BASE = '/content/drive/MyDrive/Beca Colaboracion 2024-2025/10_Resultados Simulaciones/Results_Comparison_v3_Individuales'
MPA_TO_MMHG = 7500.62
USE_FIXED_RPT_FILES = True

# --- Configuración de Identificación ---
NO_HELMET_KEYWORDS = ['nohelmet', 'sincasco', 'nahum']
HELMET_KEYWORDS = ['helmet', 'concasco', 'base']
NAHUM_SIM_IDENTIFIER = 'nahum'

# --- Configuración de Archivos ---
ACCEL_COMPONENTS_RPT_NAMES_ORIGINAL = {
    'A1': 'A1_Acc_mean.rpt', 'A2': 'A2_Acc_mean.rpt', 'A3': 'A3_Acc_mean.rpt'
}
MAGNITUDE_ACCEL_RPT_BASENAME = 'Magnitude_Acc_mean'
PRESSURE_COUP_RPT_SUFFIX_BASE = "_Pressure_FRONTREF_mean"
PRESSURE_CONTRECOUP_RPT_SUFFIX_BASE = "_Pressure_BACKREF_mean"

TIME_COLUMN_INDEX = 0
VALUE_COLUMN_INDEX = 1
RPT_IGNORE_LINE_PATTERNS = [r'^\s*\*+', r'^\s*END STEP', r'^\s*THE ANALYSIS', r'^\s*FIELD OUTPUT']

sns.set_theme(style="ticks", palette="deep")
INDIVIDUAL_COMPARISON_PALETTE = sns.color_palette("deep", n_colors=4)

NAHUM_MAX_SIMS_PER_GROUP = 5 # Usado para los colores y estilos
NAHUM_COUP_COLORS = sns.color_palette("Blues_d", n_colors=NAHUM_MAX_SIMS_PER_GROUP)
NAHUM_CONTRECOUP_COLORS = sns.color_palette("Reds_d", n_colors=NAHUM_MAX_SIMS_PER_GROUP)
NAHUM_LINE_STYLES = ['-', '--', '-.', ':', (0, (3, 1, 1, 1))]

# --- FUNCIÓN extract_title_info ---
def extract_title_info(sim_name: str, using_fixed_data: bool = False) -> Tuple[str, Optional[float], str]:
    sim_name_lower = sim_name.lower()
    display_status = "Impacto Desconocido"
    status_keyword_for_short_id = None

    if NAHUM_SIM_IDENTIFIER in sim_name_lower:
        display_status = "Nahum (Frontal)"
        match_kw = re.search(f'({NAHUM_SIM_IDENTIFIER})', sim_name, re.IGNORECASE)
        status_keyword_for_short_id = match_kw.group(1) if match_kw else "Nahum"
    elif any(keyword in sim_name_lower for keyword in HELMET_KEYWORDS):
        display_status = "Con Casco"
        for kw in HELMET_KEYWORDS:
            if kw in sim_name_lower:
                match_kw = re.search(f'({kw})', sim_name, re.IGNORECASE)
                if match_kw: status_keyword_for_short_id = match_kw.group(1); break
        if not status_keyword_for_short_id: status_keyword_for_short_id = "ConCasco"
    elif any(keyword in sim_name_lower for keyword in NO_HELMET_KEYWORDS if keyword != NAHUM_SIM_IDENTIFIER):
        display_status = "Sin Casco"
        for kw in NO_HELMET_KEYWORDS:
            if kw == NAHUM_SIM_IDENTIFIER: continue
            if kw in sim_name_lower:
                match_kw = re.search(f'({kw})', sim_name, re.IGNORECASE)
                if match_kw: status_keyword_for_short_id = match_kw.group(1); break
        if not status_keyword_for_short_id: status_keyword_for_short_id = "SinCasco"

    velocity_m_s: Optional[float] = None
    velocity_part_for_short_id = None
    match_vel = re.search(r'_?[vV](\d+)', sim_name)
    if match_vel:
        velocity_part_for_short_id = match_vel.group(0).replace("_","")
        try:
            velocity_mm_s = int(match_vel.group(1))
            velocity_m_s = velocity_mm_s / 1000.0
        except ValueError:
            print(f"    AVISO (extract_title_info): No se pudo convertir velocidad '{match_vel.group(1)}' para {sim_name}")

    short_id_list = [sid for sid in [status_keyword_for_short_id, velocity_part_for_short_id] if sid]
    short_id = "_".join(short_id_list)
    if not short_id:
        parts = sim_name.split('_'); p1 = parts[1] if len(parts) > 1 else sim_name; pL = parts[-1] if len(parts) > 1 else ""
        short_id = (f"{p1}_{pL}" if p1.lower()!=pL.lower() and pL else p1)[:20] or sim_name[:20] or "UnknownSim"

    if using_fixed_data:
        display_status += " [Corregido]"
        short_id += "_FIXED"
    return display_status, velocity_m_s, short_id

# --- Funciones Auxiliares ---
def find_rpt_file_flexible(directory: str, primary_suffix: str, secondary_name: Optional[str] = None) -> Optional[str]:
    sim_name = os.path.basename(directory)
    expected_filename_option1 = sim_name + primary_suffix
    if os.path.exists(os.path.join(directory, expected_filename_option1)):
        return os.path.join(directory, expected_filename_option1)
    if secondary_name and os.path.exists(os.path.join(directory, secondary_name)):
        return os.path.join(directory, secondary_name)
    if primary_suffix.startswith("_"):
        fallback_name = primary_suffix[1:]
        if os.path.exists(os.path.join(directory, fallback_name)):
            return os.path.join(directory, fallback_name)
    try:
        for fname in os.listdir(directory):
            if fname.endswith(primary_suffix) or \
               (primary_suffix.lower() in fname.lower() and fname.endswith(".rpt")):
                return os.path.join(directory, fname)
    except FileNotFoundError: pass
    return None

def read_rpt_data(file_path: str) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    if not file_path or not os.path.exists(file_path): return None
    time_data, value_data = [], []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_content in f:
                line = line_content.strip()
                if not line or any(re.search(p, line, re.I) for p in RPT_IGNORE_LINE_PATTERNS): continue
                try:
                    parts = re.split(r'\s+', line)
                    if len(parts) > max(TIME_COLUMN_INDEX, VALUE_COLUMN_INDEX):
                        time_data.append(float(parts[TIME_COLUMN_INDEX]))
                        value_data.append(float(parts[VALUE_COLUMN_INDEX]))
                except ValueError: continue
        return (np.array(time_data) * 1000, np.array(value_data)) if time_data and value_data else None
    except Exception as e:
        print(f"      ERROR (read_rpt_data): Fallo en {file_path}: {e}"); traceback.print_exc()
        return None

def calculate_acceleration_magnitude(dir_path: str, sim_name: str, use_fixed_file: bool) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    common_time_ms, magnitude_m_s2 = None, None
    m_s2_conv = 1.0 / 1000.0
    if use_fixed_file:
        f_path = os.path.join(dir_path, f"{MAGNITUDE_ACCEL_RPT_BASENAME}_fixed.rpt")
        data = read_rpt_data(f_path)
        if data:
            common_time_ms, mag_mm_s2 = data; magnitude_m_s2 = mag_mm_s2 * m_s2_conv
        else:
            return None
    else:
        comp_vals_m_s2: Dict[str, np.ndarray] = {}
        min_l = float('inf')
        common_time_ms = None
        for key, rpt_name in ACCEL_COMPONENTS_RPT_NAMES_ORIGINAL.items():
            data = read_rpt_data(os.path.join(dir_path, rpt_name))
            if not data:
                return None
            curr_t_ms, curr_v_mm_s2 = data
            comp_vals_m_s2[key] = curr_v_mm_s2 * m_s2_conv
            if common_time_ms is None: common_time_ms = curr_t_ms
            elif len(curr_t_ms) != len(common_time_ms) or not np.allclose(common_time_ms, curr_t_ms, atol=1e-3):
                new_min_l = min(len(common_time_ms), len(curr_t_ms))
                if not np.allclose(common_time_ms[:new_min_l], curr_t_ms[:new_min_l], atol=1e-3):
                    return None
                common_time_ms = common_time_ms[:new_min_l]; min_l = new_min_l
                for k_prev in comp_vals_m_s2: 
                    if k_prev != key:
                       comp_vals_m_s2[k_prev] = comp_vals_m_s2[k_prev][:min_l]
            min_l = min(min_l, len(comp_vals_m_s2[key]))

        if len(comp_vals_m_s2) != 3 or common_time_ms is None: return None
        
        common_time_ms = common_time_ms[:min_l]
        a1 = comp_vals_m_s2['A1'][:min_l]
        a2 = comp_vals_m_s2['A2'][:min_l]
        a3 = comp_vals_m_s2['A3'][:min_l]

        if not all(len(arr) == min_l for arr in [a1,a2,a3,common_time_ms]): return None
        magnitude_m_s2 = np.sqrt(a1**2 + a2**2 + a3**2)
    return (common_time_ms, magnitude_m_s2) if common_time_ms is not None and magnitude_m_s2 is not None else None

# --- get_simulation_data ---
def get_simulation_data(dir_path: str, use_fixed_files: bool) -> Optional[Dict[str, Any]]:
    sim_name = os.path.basename(dir_path)
    accel_data = calculate_acceleration_magnitude(dir_path, sim_name, use_fixed_files)
    time_acc_ms, acc_mag_m_s2 = (None, None) if accel_data is None else accel_data

    fixed_suffix_for_read = "_fixed.rpt" if use_fixed_files else ".rpt"
    
    def find_pressure_file(base_suffix_const):
        fname_option1 = base_suffix_const[1:] + fixed_suffix_for_read
        fpath1 = os.path.join(dir_path, fname_option1)
        if os.path.exists(fpath1): return fpath1
        
        fname_option2 = sim_name + base_suffix_const + fixed_suffix_for_read
        fpath2 = os.path.join(dir_path, fname_option2)
        if os.path.exists(fpath2): return fpath2

        if use_fixed_files:
            fname_option3_orig_suffix = base_suffix_const[1:] + ".rpt"
            fpath3 = os.path.join(dir_path, fname_option3_orig_suffix)
            if os.path.exists(fpath3): return fpath3

            fname_option4_orig_suffix = sim_name + base_suffix_const + ".rpt"
            fpath4 = os.path.join(dir_path, fname_option4_orig_suffix)
            if os.path.exists(fpath4): return fpath4
        return None

    pressure_coup_file = find_pressure_file(PRESSURE_COUP_RPT_SUFFIX_BASE)
    pressure_contrecoup_file = find_pressure_file(PRESSURE_CONTRECOUP_RPT_SUFFIX_BASE)
    
    pressure_coup_data = read_rpt_data(pressure_coup_file)
    pressure_contrecoup_data = read_rpt_data(pressure_contrecoup_file)

    if time_acc_ms is None and pressure_coup_data is None and pressure_contrecoup_data is None:
        return None
    
    display_status, velocity_m_s, short_id = extract_title_info(sim_name, use_fixed_files)

    return {
        'name': sim_name, 'dir_path': dir_path,
        'helmet_status': display_status,
        'velocity_m_s': velocity_m_s, 'short_id': short_id,
        'time_acc_ms': time_acc_ms, 'acc_mag_m_s2': acc_mag_m_s2,
        'time_p_coup_ms': pressure_coup_data[0] if pressure_coup_data else None,
        'pressure_coup_mpa': pressure_coup_data[1] if pressure_coup_data else None,
        'time_p_contrecoup_ms': pressure_contrecoup_data[0] if pressure_contrecoup_data else None,
        'pressure_contrecoup_mpa': pressure_contrecoup_data[1] if pressure_contrecoup_data else None,
    }

# --- Funciones de Graficación Individual ---
def plot_individual_pressures_coup_contrecoup(sim_data: Dict[str, Any], results_dir: str, use_fixed_files: bool):
    name = sim_data['name']
    plot_desc = sim_data.get('helmet_status', 'Impacto Desconocido')
    velocity_m_s = sim_data.get('velocity_m_s')
    short_id = sim_data.get('short_id', re.sub(r'[^\w\-_\.]', '_', name[:20]))
    
    vel_str = f"@ {velocity_m_s:.2f} m/s" if velocity_m_s is not None else "(Vel. desconocida)"
    main_title = f"{plot_desc} {vel_str}\nPresión Intracraneal (Coup y Contrecoup)"
    
    fig, ax_mpa = plt.subplots(figsize=(12, 7)); plt.title(main_title, fontsize=15, fontweight='bold')
    lines_for_legend = []
    if sim_data['time_p_coup_ms'] is not None and sim_data['pressure_coup_mpa'] is not None:
        l, = ax_mpa.plot(sim_data['time_p_coup_ms'], sim_data['pressure_coup_mpa'], c=INDIVIDUAL_COMPARISON_PALETTE[1], ls='--', lw=2, label='Presión Coup (Front) [MPa]'); lines_for_legend.append(l)
    if sim_data['time_p_contrecoup_ms'] is not None and sim_data['pressure_contrecoup_mpa'] is not None:
        l, = ax_mpa.plot(sim_data['time_p_contrecoup_ms'], sim_data['pressure_contrecoup_mpa'], c=INDIVIDUAL_COMPARISON_PALETTE[2], ls=':', lw=2, label='Presión Contrecoup (Back) [MPa]'); lines_for_legend.append(l)
    
    ax_mpa.set_xlabel('Tiempo (ms)', fontsize=12); ax_mpa.set_ylabel('Presión (MPa)', fontsize=12, color='black')
    ax_mpa.tick_params(axis='y', labelcolor='black')
    ax_mmhg = ax_mpa.twinx()
    if lines_for_legend:
        ax_mmhg.set_ylabel('Presión (mmHg)', fontsize=12, color='black'); ax_mmhg.tick_params(axis='y', labelcolor='black'); fig.canvas.draw()
        ymin, ymax = ax_mpa.get_ylim(); 
        if ymin == ymax: ymin, ymax = (ymin - 0.01, ymax + 0.01) if ymin !=0 else (-0.001, 0.001)
        ax_mpa.set_ylim(ymin, ymax); fig.canvas.draw(); ax_mmhg.set_ylim(ymin * MPA_TO_MMHG, ymax * MPA_TO_MMHG)
        ax_mpa.legend(loc='upper right', fontsize=10, frameon=True, facecolor='white', framealpha=0.8)
    else: 
        ax_mmhg.set_yticks([]); ax_mmhg.set_yticklabels([]); ax_mmhg.set_ylabel("")
        ax_mpa.text(0.5, 0.5, "No hay datos de presión.", ha='center', va='center', transform=ax_mpa.transAxes)
    
    fig.tight_layout(); base_fn = os.path.join(results_dir, f"Individual_Pressures_CoupContrecoup_{short_id}")
    plt.savefig(f"{base_fn}.png", dpi=300); plt.savefig(f"{base_fn}.eps", format='eps', bbox_inches='tight'); plt.close(fig)

def plot_individual_accel_and_pressures_coup_contrecoup(sim_data: Dict[str, Any], results_dir: str, use_fixed_files: bool):
    name = sim_data['name']
    plot_desc = sim_data.get('helmet_status', 'Impacto Desconocido')
    velocity_m_s = sim_data.get('velocity_m_s')
    short_id = sim_data.get('short_id', re.sub(r'[^\w\-_\.]', '_', name[:20]))
    
    vel_str = f"@ {velocity_m_s:.2f} m/s" if velocity_m_s is not None else "(Vel. desconocida)"
    main_title = f"{plot_desc} {vel_str}\nAceleración y Presión Intracraneal"

    fig, ax1 = plt.subplots(figsize=(14, 8)); plt.title(main_title, fontsize=15, fontweight='bold')
    lines = []
    acc_label = 'Aceleración Mag. (m/s²)'
    if sim_data['time_acc_ms'] is not None and sim_data['acc_mag_m_s2'] is not None:
        l, = ax1.plot(sim_data['time_acc_ms'], sim_data['acc_mag_m_s2'], c=INDIVIDUAL_COMPARISON_PALETTE[0], ls='-', lw=2, label=acc_label); lines.append(l)
    
    ax1.set_xlabel('Tiempo (ms)', fontsize=12); ax1.set_ylabel(acc_label, color=INDIVIDUAL_COMPARISON_PALETTE[0], fontsize=12)
    ax1.tick_params(axis='y', labelcolor=INDIVIDUAL_COMPARISON_PALETTE[0])
    
    ax2 = ax1.twinx(); p_exists = False
    if sim_data['time_p_coup_ms'] is not None and sim_data['pressure_coup_mpa'] is not None:
        l, = ax2.plot(sim_data['time_p_coup_ms'], sim_data['pressure_coup_mpa'], c=INDIVIDUAL_COMPARISON_PALETTE[1], ls='--', lw=2, label='Presión Coup (Front) [MPa]'); lines.append(l); p_exists = True
    if sim_data['time_p_contrecoup_ms'] is not None and sim_data['pressure_contrecoup_mpa'] is not None:
        l, = ax2.plot(sim_data['time_p_contrecoup_ms'], sim_data['pressure_contrecoup_mpa'], c=INDIVIDUAL_COMPARISON_PALETTE[2], ls=':', lw=2, label='Presión Contrecoup (Back) [MPa]'); lines.append(l); p_exists = True
    
    ax2.set_ylabel('Presión (MPa)', fontsize=12, color='black'); ax2.tick_params(axis='y', labelcolor='black')
    ax3 = ax1.twinx(); ax3.spines["right"].set_position(("outward", 70)); ax3.spines["right"].set_visible(True)
    if p_exists:
        ax3.set_ylabel('Presión (mmHg)', fontsize=12, color='black'); ax3.tick_params(axis='y', labelcolor='black'); fig.canvas.draw()
        ymin, ymax = ax2.get_ylim();
        if ymin == ymax: ymin, ymax = (ymin - 0.01, ymax + 0.01) if ymin !=0 else (-0.001, 0.001)
        ax2.set_ylim(ymin, ymax); fig.canvas.draw(); ax3.set_ylim(ymin * MPA_TO_MMHG, ymax * MPA_TO_MMHG)
    else: 
        ax2.set_yticks([]); ax2.set_yticklabels([]); ax2.set_ylabel("")
        ax3.set_yticks([]); ax3.set_yticklabels([]); ax3.set_ylabel("")
    
    if lines: ax1.legend(loc='upper right', fontsize=10, frameon=True, facecolor='white', framealpha=0.8)
    elif not (sim_data.get('acc_mag_m_s2') is not None) and not p_exists: ax1.text(0.5,0.5,"No hay datos.", ha='center',va='center',transform=ax1.transAxes)
    elif not (sim_data.get('acc_mag_m_s2') is not None): ax1.text(0.5,0.5,"No hay datos de aceleración.", ha='center',va='center',transform=ax1.transAxes)
    
    fig.tight_layout(); fig.subplots_adjust(right=0.78)
    base_fn = os.path.join(results_dir, f"Individual_AccAndPressures_CoupContrecoup_{short_id}")
    plt.savefig(f"{base_fn}.png", dpi=300); plt.savefig(f"{base_fn}.eps", format='eps', bbox_inches='tight'); plt.close(fig)

# --- Funciones de Graficación Comparativa Nahum ---
def plot_nahum_comparative_pressure_series_single_type(
    sim_data_group: List[Dict[str, Any]], pressure_type: str,
    group_identifier: str, results_dir: str, use_fixed_files: bool
):
    if not sim_data_group: return

    fig, ax_mpa = plt.subplots(figsize=(12, 7))
    p_type_display = "Coup" if pressure_type == "coup" else "Contrecoup"
    
    group_velocities_m_s = sorted([s['velocity_m_s'] for s in sim_data_group if s.get('velocity_m_s') is not None])
    title_vel_range_str = f"{group_velocities_m_s[0]:.2f} m/s a {group_velocities_m_s[-1]:.2f} m/s" if group_velocities_m_s else "Velocidades Variadas"
    fixed_display_suffix = " [Corregido]" if use_fixed_files else ""
    
    group_name_for_title = group_identifier.split('_Vels_')[0].replace('_', ' ') if '_Vels_' in group_identifier else group_identifier.replace('_', ' ')
    main_title_line2 = f"Velocidades: {title_vel_range_str}" if group_velocities_m_s else title_vel_range_str
    main_title = f"Nahum: Presión {p_type_display} - {group_name_for_title}{fixed_display_suffix}\n{main_title_line2}"
    plt.title(main_title, fontsize=14, fontweight='bold')

    lines_for_legend = []
    for i, sim_data in enumerate(sim_data_group):
        time_k, pressure_k = f'time_p_{pressure_type}_ms', f'pressure_{pressure_type}_mpa'
        if sim_data.get(time_k) is not None and sim_data.get(pressure_k) is not None:
            vel_m_s_actual = sim_data.get('velocity_m_s')
            label = f"{vel_m_s_actual:.3f} m/s" if vel_m_s_actual is not None else f"Sim {i+1}"
            color_to_use = NAHUM_COUP_COLORS[i % len(NAHUM_COUP_COLORS)]
            l, = ax_mpa.plot(sim_data[time_k], sim_data[pressure_k], 
                             color=color_to_use, 
                             linestyle=NAHUM_LINE_STYLES[i % len(NAHUM_LINE_STYLES)], 
                             lw=2, label=label)
            lines_for_legend.append(l)

    ax_mpa.set_xlabel('Tiempo (ms)', fontsize=12); ax_mpa.set_ylabel('Presión (MPa)', fontsize=12, color='black')
    ax_mpa.tick_params(axis='y', labelcolor='black')
    ax_mmhg = ax_mpa.twinx()

    if lines_for_legend:
        ax_mmhg.set_ylabel('Presión (mmHg)', fontsize=12, color='black'); ax_mmhg.tick_params(axis='y', labelcolor='black'); fig.canvas.draw()
        ymin, ymax = ax_mpa.get_ylim();
        if ymin == ymax: ymin, ymax = (ymin - 0.01, ymax + 0.01) if ymin !=0 else (-0.001, 0.001)
        ax_mpa.set_ylim(ymin, ymax); fig.canvas.draw(); ax_mmhg.set_ylim(ymin * MPA_TO_MMHG, ymax * MPA_TO_MMHG)
        ax_mpa.legend(loc='upper right', title="Velocidad Impacto", fontsize=10, title_fontsize=11, frameon=True, facecolor='white', framealpha=0.8)
    else: 
        ax_mmhg.set_yticks([]); ax_mmhg.set_yticklabels([]); ax_mmhg.set_ylabel("")
        ax_mpa.text(0.5,0.5, f"No hay datos de presión {p_type_display} para este grupo.", ha='center',va='center',transform=ax_mpa.transAxes)
    
    fig.tight_layout()
    fname_base = f"Nahum_Comparative_{p_type_display}_Only_{group_identifier}{'_FIXED' if use_fixed_files else ''}"
    full_path_base = os.path.join(results_dir, fname_base)
    plt.savefig(f"{full_path_base}.png", dpi=300); plt.savefig(f"{full_path_base}.eps", format='eps', bbox_inches='tight'); plt.close(fig)

# MODIFICADO: Ahora la función puede manejar grupos de cualquier tamaño (1, 2, o más como antes)
# El nombre del archivo y el título se ajustarán según el contexto de la llamada.
def plot_nahum_comparative_coup_contrecoup_combined(
    sim_data_group: List[Dict[str, Any]], 
    group_identifier: str, # Será "Grupo_1_Vels_...", "Grupo_2_Vels_...", "Par_V1_vs_V2", o "Solo_V3"
    results_dir: str,
    use_fixed_files: bool,
    is_pair_or_solo_plot: bool = False # NUEVO: Para diferenciar el tipo de título y nombre de archivo
):
    if not sim_data_group: return

    fig, ax_mpa = plt.subplots(figsize=(13, 8))
    
    group_velocities_m_s = sorted([s['velocity_m_s'] for s in sim_data_group if s.get('velocity_m_s') is not None])
    
    title_vel_range_str = ""
    if not group_velocities_m_s:
        title_vel_range_str = "Velocidades Desconocidas"
    elif len(group_velocities_m_s) == 1:
        title_vel_range_str = f"{group_velocities_m_s[0]:.2f} m/s"
    elif len(group_velocities_m_s) == 2 and is_pair_or_solo_plot : # Solo para el caso de par/solo, mostrar "y"
        title_vel_range_str = f"{group_velocities_m_s[0]:.2f} m/s y {group_velocities_m_s[1]:.2f} m/s"
    else: # Para grupos grandes o si no es par/solo, mostrar rango
        title_vel_range_str = f"{group_velocities_m_s[0]:.2f} m/s a {group_velocities_m_s[-1]:.2f} m/s"

    fixed_display_suffix = " [Corregido]" if use_fixed_files else ""

    title_prefix = "Nahum: Presión Coup & Contrecoup"
    main_title_line2 = f"Velocidades: {title_vel_range_str}" # Para grupos grandes
    
    if is_pair_or_solo_plot:
        sim_count_in_group = len(sim_data_group)
        if sim_count_in_group == 1:
            title_prefix = "Nahum: Simulación Individual (Presión Coup & Contrecoup)"
        elif sim_count_in_group == 2:
            title_prefix = "Nahum: Comparativa Par (Presión Coup & Contrecoup)"
        main_title_line2 = f"Simulaciones: {title_vel_range_str}" # Para pares/solos
    else: # Es un grupo grande (Grupo_1, Grupo_2)
        group_name_for_title = group_identifier.split('_Vels_')[0].replace('_', ' ') if '_Vels_' in group_identifier else group_identifier.replace('_', ' ')
        title_prefix = f"Nahum: Presión Coup & Contrecoup - {group_name_for_title}"

    main_title = f"{title_prefix}{fixed_display_suffix}\n{main_title_line2}"
    plt.title(main_title, fontsize=14, fontweight='bold')

    lines_for_legend = []
    num_unique_sims_in_group = len(sim_data_group)

    for i, sim_data in enumerate(sim_data_group):
        vel_m_s_actual = sim_data.get('velocity_m_s')
        vel_label_part = f"{vel_m_s_actual:.3f} m/s" if vel_m_s_actual is not None else f"Sim {i+1}"
        
        style_idx = i 
        
        current_style = NAHUM_LINE_STYLES[style_idx % len(NAHUM_LINE_STYLES)]
        coup_color = NAHUM_COUP_COLORS[style_idx % len(NAHUM_COUP_COLORS)]
        contrecoup_color = NAHUM_CONTRECOUP_COLORS[style_idx % len(NAHUM_CONTRECOUP_COLORS)]

        if sim_data.get('time_p_coup_ms') is not None and sim_data.get('pressure_coup_mpa') is not None:
            l_coup, = ax_mpa.plot(sim_data['time_p_coup_ms'], sim_data['pressure_coup_mpa'], 
                                  color=coup_color, linestyle=current_style, 
                                  lw=2, label=f'{vel_label_part} - Coup')
            lines_for_legend.append(l_coup)

        if sim_data.get('time_p_contrecoup_ms') is not None and sim_data.get('pressure_contrecoup_mpa') is not None:
            l_cont, = ax_mpa.plot(sim_data['time_p_contrecoup_ms'], sim_data['pressure_contrecoup_mpa'], 
                                  color=contrecoup_color, linestyle=current_style, 
                                  lw=2, label=f'{vel_label_part} - Contrecoup')
            lines_for_legend.append(l_cont)

    ax_mpa.set_xlabel('Tiempo (ms)', fontsize=12); ax_mpa.set_ylabel('Presión (MPa)', fontsize=12, color='black')
    ax_mpa.tick_params(axis='y', labelcolor='black')
    ax_mmhg = ax_mpa.twinx()

    if lines_for_legend:
        ax_mmhg.set_ylabel('Presión (mmHg)', fontsize=12, color='black'); ax_mmhg.tick_params(axis='y', labelcolor='black'); fig.canvas.draw()
        ymin, ymax = ax_mpa.get_ylim();
        if ymin == ymax: ymin, ymax = (ymin - 0.01, ymax + 0.01) if ymin !=0 else (-0.001, 0.001)
        ax_mpa.set_ylim(ymin, ymax); fig.canvas.draw(); ax_mmhg.set_ylim(ymin * MPA_TO_MMHG, ymax * MPA_TO_MMHG)
        
        legend_ncols = 1 if num_unique_sims_in_group == 1 else 2 # 2 columnas si hay más de 1 simulación
        ax_mpa.legend(loc='upper right', title="Velocidad - Tipo", fontsize=9, title_fontsize=10, frameon=True, facecolor='white', framealpha=0.8, ncol=legend_ncols)
    else: 
        ax_mmhg.set_yticks([]); ax_mmhg.set_yticklabels([]); ax_mmhg.set_ylabel("")
        ax_mpa.text(0.5,0.5, "No hay datos de presión Coup/Contrecoup para este grupo.", ha='center',va='center',transform=ax_mpa.transAxes)
    
    fig.tight_layout()
    # El nombre del archivo ya se construye correctamente en main() antes de llamar a esta función
    fname_prefix = "Nahum_Comparative_CoupContrecoup_Combined"
    if is_pair_or_solo_plot:
        fname_prefix = "Nahum_PairSolo_CoupContrecoup_Combined" # Distinguir nombres de archivo
        
    fname_base = f"{fname_prefix}_{group_identifier}{'_FIXED' if use_fixed_files else ''}"
    full_path_base = os.path.join(results_dir, fname_base)
    plt.savefig(f"{full_path_base}.png", dpi=300); plt.savefig(f"{full_path_base}.eps", format='eps', bbox_inches='tight'); plt.close(fig)


# --- Lógica Principal ---
def main():
    results_dir = RESULTS_COMPARISON_DIR_BASE + ("_CorrectedData" if USE_FIXED_RPT_FILES else "_OriginalData")
    print(f"\n--- Iniciando Script (Datos Corregidos: {USE_FIXED_RPT_FILES}) ---")
    print(f"Directorio de Reportes: {REPORTS_ROOT_DIR}\nDirectorio de Salida: {results_dir}")
    if not os.path.exists(REPORTS_ROOT_DIR): print(f"ERROR: El directorio de reportes '{REPORTS_ROOT_DIR}' no existe."); return
    os.makedirs(results_dir, exist_ok=True)

    all_sim_dirs = [d for d in os.listdir(REPORTS_ROOT_DIR) if os.path.isdir(os.path.join(REPORTS_ROOT_DIR, d))]
    if not all_sim_dirs: print("No se encontraron directorios de simulación en el directorio de reportes."); return

    all_sim_data: List[Dict[str, Any]] = []
    print(f"\n--- Procesando {len(all_sim_dirs)} Directorios de Simulación ---")
    for i, sim_dir_name in enumerate(sorted(all_sim_dirs)):
        sim_data_item = get_simulation_data(os.path.join(REPORTS_ROOT_DIR, sim_dir_name), USE_FIXED_RPT_FILES)
        if sim_data_item:
            all_sim_data.append(sim_data_item)
    
    if not all_sim_data:
        print("No se pudieron procesar datos de ninguna simulación.")
        return

    processed_individual_count = 0
    print(f"\n--- Generando Gráficas Individuales para {len(all_sim_data)} simulaciones procesadas ---")
    for sim_data in all_sim_data:
        has_p = sim_data.get('pressure_coup_mpa') is not None or sim_data.get('pressure_contrecoup_mpa') is not None
        has_a = sim_data.get('acc_mag_m_s2') is not None
        
        if has_p: 
            plot_individual_pressures_coup_contrecoup(sim_data, results_dir, USE_FIXED_RPT_FILES)
        if has_a or has_p: 
            plot_individual_accel_and_pressures_coup_contrecoup(sim_data, results_dir, USE_FIXED_RPT_FILES)
            processed_individual_count+=1
    print(f"--- Gráficas Individuales Generadas: {processed_individual_count} simulaciones con datos suficientes graficadas. ---")

    print(f"\n--- Generando Gráficos Comparativos de Presión para Simulaciones Nahum ---")
    
    nahum_sims = [s for s in all_sim_data if 
                  (s.get('helmet_status') and NAHUM_SIM_IDENTIFIER in s['helmet_status'].lower()) or
                  (NAHUM_SIM_IDENTIFIER in s.get('name','').lower())]

    if not nahum_sims:
        print("  No se encontraron simulaciones Nahum para los gráficos comparativos.");
    else:
        print(f"  Se encontraron {len(nahum_sims)} simulaciones Nahum. Ordenando por velocidad...")
        nahum_sims.sort(key=lambda s: s.get('velocity_m_s', float('inf')) if s.get('velocity_m_s') is not None else float('inf'))
        
        # Grupos grandes para "Solo Coup", "Solo Contrecoup" y "Coup&Contrecoup Combinado por Grupo"
        group1_sims_large = nahum_sims[0::2]
        group2_sims_large = nahum_sims[1::2]
        sim_groups_for_large_plots = {"Grupo_1": group1_sims_large, "Grupo_2": group2_sims_large}

        print("\n  Generando gráficas comparativas Nahum por grupos grandes (Solo Coup, Solo Contrecoup, Combinado):")
        for group_key_name, current_large_group in sim_groups_for_large_plots.items():
            if not current_large_group:
                print(f"    {group_key_name} de Nahum para gráficas de grupo grande está vacío, omitiendo.")
                continue

            group_vels_m_s_large = sorted([s['velocity_m_s'] for s in current_large_group if s.get('velocity_m_s') is not None])
            group_id_str_large = group_key_name
            if group_vels_m_s_large:
                 group_id_str_large += f"_Vels_{group_vels_m_s_large[0]:.2f}_a_{group_vels_m_s_large[-1]:.2f}mps".replace(".","p")
            else:
                 group_id_str_large += "_Vels_Variadas"
            
            print(f"    Procesando {group_key_name} ({len(current_large_group)} sims) ID: {group_id_str_large}")
            # Solo Coup
            plot_nahum_comparative_pressure_series_single_type(current_large_group, "coup", group_id_str_large, results_dir, USE_FIXED_RPT_FILES)
            # Solo Contrecoup
            plot_nahum_comparative_pressure_series_single_type(current_large_group, "contrecoup", group_id_str_large, results_dir, USE_FIXED_RPT_FILES)
            # Coup & Contrecoup Combinado por Grupo Grande
            plot_nahum_comparative_coup_contrecoup_combined(
                current_large_group, 
                group_id_str_large, 
                results_dir, 
                USE_FIXED_RPT_FILES, 
                is_pair_or_solo_plot=False # MODIFICADO: Indicar que NO es un gráfico de par/solo
            )
            print(f"      Gráficas de grupo grande para {group_key_name} guardadas.")

        # Gráficas combinadas Coup-Contrecoup de 2 en 2 (o individual)
        print(f"\n  Generando gráficas comparativas Nahum (Coup-Contrecoup Combinado) por pares/individuales...")
        num_nahum_sims = len(nahum_sims)
        plotted_pair_solo_combined_count = 0
        for i in range(0, num_nahum_sims, 2):
            current_pair_group = nahum_sims[i : i + 2]
            if not current_pair_group:
                continue

            group_id_str_pair_solo = ""
            cleaned_ids = []
            for sim_in_pair in current_pair_group:
                s_id = sim_in_pair['short_id'].replace("_FIXED","")
                s_id = s_id.replace(NAHUM_SIM_IDENTIFIER.capitalize() + "_", "")
                s_id = s_id.replace(NAHUM_SIM_IDENTIFIER + "_", "")
                s_id = s_id.replace("_", "")
                cleaned_ids.append(s_id)

            if len(cleaned_ids) == 2:
                group_id_str_pair_solo = f"Par_{cleaned_ids[0]}_vs_{cleaned_ids[1]}"
            elif len(cleaned_ids) == 1:
                group_id_str_pair_solo = f"Solo_{cleaned_ids[0]}"
            
            print(f"    Procesando par/individual de Nahum para gráfico combinado (ID: {group_id_str_pair_solo})")
            plot_nahum_comparative_coup_contrecoup_combined(
                current_pair_group, 
                group_id_str_pair_solo, 
                results_dir, 
                USE_FIXED_RPT_FILES,
                is_pair_or_solo_plot=True # MODIFICADO: Indicar que SÍ es un gráfico de par/solo
            )
            plotted_pair_solo_combined_count +=1
            print(f"      Gráfica combinada par/solo para '{group_id_str_pair_solo}' guardada.")
        
        if plotted_pair_solo_combined_count > 0:
             print(f"  Se generaron {plotted_pair_solo_combined_count} gráficas combinadas de Nahum (pares/individuales).")

    print(f"\n--- Proceso Completado. Resultados en: '{results_dir}' ---")

if __name__ == '__main__':
    main()
