# -*- coding: mbcs -*-
# SCRIPT PYTHON PARA VERIFICAR ESTADO DE ARCHIVOS .STA DE ABAQUS

# --- Importaciones ---
import os         # Para interactuar con el sistema operativo (archivos, directorios)
import glob       # Para encontrar archivos que coincidan con un patron (ej. *.sta)
import traceback  # Para imprimir detalles de errores inesperados

# --- Constantes ---
# Frases a buscar dentro de los archivos .sta
SUCCESS_PHRASE = "THE ANALYSIS HAS COMPLETED SUCCESSFULLY"
FAILURE_PHRASE = "THE ANALYSIS HAS NOT BEEN COMPLETED" # Cubre tambien errores explicitos

# Nombre de la carpeta y archivo de salida
STATUS_DIR_NAME = "Status"
STATUS_FILE_NAME = "analysis_status.txt"

# Mensajes de estado para el archivo de salida
STATUS_OK = "EJECUTADO CORRECTAMENTE"
STATUS_FAIL = "NO COMPLETADO O FALLIDO"
STATUS_UNKNOWN = "ESTADO DESCONOCIDO (frase no encontrada)"

# --- Funcion Principal ---
def check_analysis_status():
    """
    Busca archivos .sta en el directorio actual, verifica su estado de finalizacion
    y genera un archivo de reporte con los resultados.
    """
    script_dir = os.getcwd() # Obtiene el directorio actual donde se ejecuta el script
    print 'INFO: Directorio de trabajo actual: %s' % script_dir

    # --- Buscar archivos .sta ---
    sta_files = glob.glob(os.path.join(script_dir, '*.sta'))

    if not sta_files:
        print 'ADVERTENCIA: No se encontraron archivos .sta en el directorio: %s' % script_dir
        print 'INFO: Saliendo del script.'
        return # Salir si no hay archivos .sta

    print 'INFO: Se encontraron %d archivos .sta:' % len(sta_files)
    # Imprimir solo los nombres de archivo, no la ruta completa
    for f_path in sta_files:
        print '  - %s' % os.path.basename(f_path)

    # --- Crear directorio de Status si no existe ---
    status_dir_path = os.path.join(script_dir, STATUS_DIR_NAME)
    if not os.path.exists(status_dir_path):
        print 'INFO: Creando directorio para el reporte: %s' % status_dir_path
        try:
            os.makedirs(status_dir_path)
        except (OSError, IOError) as e:
            print 'ERROR: No se pudo crear el directorio "%s".' % STATUS_DIR_NAME
            print '  Error: %s' % e
            print 'INFO: Saliendo del script.'
            return # Salir si no se puede crear el directorio
    else:
        print 'INFO: El directorio "%s" ya existe.' % STATUS_DIR_NAME

    # --- Procesar cada archivo .sta ---
    status_report_path = os.path.join(status_dir_path, STATUS_FILE_NAME)
    print 'INFO: Escribiendo reporte de estado en: %s' % status_report_path

    try:
        # Abrir el archivo de reporte en modo escritura ('w')
        # Esto sobrescribira el archivo si ya existe
        with open(status_report_path, 'w') as report_file:
            report_file.write("--- Reporte de Estado de Simulaciones Abaqus ---\n")
            report_file.write("Directorio Analizado: %s\n" % script_dir)
            report_file.write("-----------------------------------------------\n\n")

            for sta_file_path in sta_files:
                sta_filename = os.path.basename(sta_file_path)
                simulation_name = os.path.splitext(sta_filename)[0] # Nombre sin extension .sta
                current_status = STATUS_UNKNOWN # Estado por defecto

                print 'INFO: Procesando archivo: %s' % sta_filename

                try:
                    # Leer el contenido del archivo .sta
                    with open(sta_file_path, 'r') as f_sta:
                        content = f_sta.read()

                    # Buscar las frases clave (insensible a mayusculas/minusculas al inicio/fin,
                    # pero las frases de Abaqus suelen ser exactas)
                    # Se busca la frase exacta incluyendo los espacios iniciales
                    if SUCCESS_PHRASE in content:
                        current_status = STATUS_OK
                        print '  - Estado encontrado: %s' % STATUS_OK
                    elif FAILURE_PHRASE in content:
                        current_status = STATUS_FAIL
                        print '  - Estado encontrado: %s' % STATUS_FAIL
                    else:
                        # Si no se encuentra ninguna de las frases exactas al final
                        # podria ser que el analisis este en curso o termino abruptamente
                        print '  - ADVERTENCIA: No se encontro la frase de exito ni la de fallo estandar.'
                        print '    El analisis podria estar incompleto, en ejecucion o haber terminado de forma anormal.'
                        current_status = STATUS_UNKNOWN # Mantenemos desconocido

                except (IOError, OSError) as e_read:
                    print '  ERROR: No se pudo leer el archivo "%s". Saltando.' % sta_filename
                    print '    Error: %s' % e_read
                    current_status = "ERROR AL LEER ARCHIVO"
                except Exception as e_unexpected:
                    print '  ERROR: Ocurrio un error inesperado al procesar "%s". Saltando.' % sta_filename
                    print '    Tipo: %s' % type(e_unexpected).__name__
                    print '    Mensaje: %s' % e_unexpected
                    print traceback.format_exc() # Imprime mas detalles del error
                    current_status = "ERROR INESPERADO"

                # Escribir la linea en el archivo de reporte
                report_line = '%s: %s\n' % (simulation_name, current_status)
                report_file.write(report_line)

        print '\nINFO: Reporte de estado generado exitosamente en "%s".' % status_report_path

    except (IOError, OSError) as e_write:
        print 'ERROR: No se pudo escribir en el archivo de reporte "%s".' % status_report_path
        print '  Error: %s' % e_write
    except Exception as e_general:
        print 'ERROR: Ocurrio un error inesperado durante la escritura del reporte.'
        print '  Tipo: %s' % type(e_general).__name__
        print '  Mensaje: %s' % e_general
        print traceback.format_exc()


# --- Punto de entrada del script ---
if __name__ == '__main__':
    print "--- Iniciando Script Verificador de Estado STA ---"
    check_analysis_status()
    print "--- Script Verificador de Estado STA Finalizado ---"
