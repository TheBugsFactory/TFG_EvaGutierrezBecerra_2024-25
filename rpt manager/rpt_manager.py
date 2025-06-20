# -*- coding: mbcs -*-
# PYTHON SCRIPT PARA EXTRACCION AUTOMATICA DE DATOS DE ODBs (v9 - Corregido Acceso a Node Labels en Array anidado)

# --- Importaciones ---
import os
import sys
import math
import traceback # Para imprimir detalles del error

# Importaciones de Abaqus (Estilo clasico para v6.12)
from abaqus import *
from abaqusConstants import *
from caeModules import *
import visualization
import xyPlot
import displayGroupOdbToolset as dgo
from odbAccess import OdbError

# --- Funcion Principal ---
def process_odb_files():
    """
    Funcion principal para encontrar y procesar archivos ODB.
    """
    # --- Configuracion (AJUSTAR SEGUN SEA NECESARIO) ---
    NODE_SET_ACC = 'SET-ACC-NODAL' # NodeSet para aceleracion
    ELEMENT_SETS_PRESSURE = [      # ElementSets para presion
        'BACKREF', 'BOTTOMREF', 'CENTREOFMASSREF',
        'FRONTREF', 'LEFTREF', 'RIGHTREF', 'TOPREF'
    ]
    # !IMPORTANTE!: Verifica que estos nombres coincidan EXACTAMENTE con tu ODB
    STEP_NAME = 'Step-1'          # Nombre del Step de interes
    INSTANCE_NAME = 'PART-1-1'    # Nombre de la instancia principal donde estan los sets/nodos
    REPORT_DIR_NAME = 'Reports'   # Nombre de la carpeta principal de reportes

    # Variables de Output
    PRESSURE_VAR = (('S', INTEGRATION_POINT, ((INVARIANT, 'Pressure'), )), )
    ACCEL_VAR_PREFIX = 'Spatial acceleration'

    # --- Inicio del Script ---
    script_dir = os.getcwd()
    print 'INFO: Buscando archivos .odb en: %s' % script_dir

    reports_base_dir = os.path.join(script_dir, REPORT_DIR_NAME)
    if not os.path.exists(reports_base_dir):
        try:
            os.makedirs(reports_base_dir)
            print 'INFO: Creado directorio de reportes: %s' % reports_base_dir
        except (OSError, IOError) as e:
            print 'ERROR: No se pudo crear el directorio de reportes: %s' % reports_base_dir
            print '  Error: %s' % e
            return

    odb_files = [f for f in os.listdir(script_dir) if f.lower().endswith('.odb')]

    if not odb_files:
        print 'WARNING: No se encontraron archivos .odb en el directorio: %s' % script_dir
        return

    print 'INFO: Se encontraron los siguientes archivos .odb: %s' % ', '.join(odb_files)

    # --- Bucle principal para procesar cada ODB ---
    for odb_file in odb_files:
        odb_path = os.path.join(script_dir, odb_file)
        odb_name_base = os.path.splitext(odb_file)[0]
        print '\nINFO: Procesando archivo: %s' % odb_file

        odb_report_dir = os.path.join(reports_base_dir, odb_name_base)
        if not os.path.exists(odb_report_dir):
            try:
                os.makedirs(odb_report_dir)
            except (OSError, IOError) as e:
                print 'ERROR: No se pudo crear el directorio para %s: %s' % (odb_name_base, odb_report_dir)
                print '  Error: %s' % e
                continue

        print 'INFO: Guardando reportes en: %s' % odb_report_dir

        odb = None
        try:
            # --- Abrir ODB y verificar componentes ---
            print 'INFO: Abriendo ODB: %s' % odb_file
            odb = session.openOdb(name=odb_path, readOnly=True)

            current_instance_name = INSTANCE_NAME
            current_step_name = STEP_NAME

            # Verificar Instancia
            if current_instance_name not in odb.rootAssembly.instances.keys():
                 if len(odb.rootAssembly.instances) > 0:
                     current_instance_name = odb.rootAssembly.instances.keys()[0]
                     print 'WARNING: La instancia "%s" no existe. Usando la primera encontrada: "%s"' % (INSTANCE_NAME, current_instance_name)
                 else:
                     print 'ERROR: No se encontraron instancias en el ODB: %s' % odb_file
                     odb.close()
                     continue

            # Verificar Step
            if current_step_name not in odb.steps.keys():
                if len(odb.steps) > 0:
                    current_step_name = odb.steps.keys()[-1]
                    print 'WARNING: El step "%s" no existe. Usando el ultimo encontrado: "%s"' % (STEP_NAME, current_step_name)
                else:
                    print 'ERROR: No se encontraron steps en el ODB: %s' % odb_file
                    odb.close()
                    continue

            print 'INFO: Usando Instancia "%s" y Step "%s"' % (current_instance_name, current_step_name)

            # --- Procesamiento de Presion (SIN CAMBIOS) ---
            print 'INFO: Procesando Presion...'
            session.viewports[session.viewports.keys()[0]].setValues(displayedObject=odb)

            for elem_set_name in ELEMENT_SETS_PRESSURE:
                # ... (codigo de presion sin cambios)...
                print '  Procesando ElementSet: %s' % elem_set_name
                elem_set_exists = False
                set_ref_for_field = None
                element_set = None

                if elem_set_name in odb.rootAssembly.elementSets.keys():
                    element_set = odb.rootAssembly.elementSets[elem_set_name]
                    if hasattr(element_set, 'elements') and len(element_set.elements) > 0:
                        elem_set_exists = True
                        set_ref_for_field = elem_set_name
                        print '  INFO: ElementSet "%s" encontrado en Assembly.' % elem_set_name
                    else:
                         print '  WARNING: ElementSet "%s" encontrado en Assembly pero VACIO o invalido. Saltando.' % elem_set_name

                elif current_instance_name in odb.rootAssembly.instances and elem_set_name in odb.rootAssembly.instances[current_instance_name].elementSets.keys():
                    element_set = odb.rootAssembly.instances[current_instance_name].elementSets[elem_set_name]
                    if hasattr(element_set, 'elements') and len(element_set.elements) > 0:
                        elem_set_exists = True
                        set_ref_for_field = odb.rootAssembly.instances[current_instance_name].elementSets[elem_set_name]
                        print '  INFO: ElementSet "%s" encontrado en Instancia "%s".' % (elem_set_name, current_instance_name)
                    else:
                        print '  WARNING: ElementSet "%s" encontrado en Instancia "%s" pero VACIO o invalido. Saltando.' % (elem_set_name, current_instance_name)
                else:
                     print '  WARNING: ElementSet "%s" no encontrado en Assembly ni en Instancia "%s". Saltando.' % (elem_set_name, current_instance_name)

                if not elem_set_exists:
                    continue

                xyList_pressure = []
                try:
                    xyList_pressure = xyPlot.xyDataListFromField(
                        odb=odb,
                        outputPosition=INTEGRATION_POINT,
                        variable=PRESSURE_VAR,
                        elementSets=(set_ref_for_field,)
                    )

                    if not xyList_pressure:
                        print '  WARNING: No se generaron datos XY para el set "%s".' % elem_set_name
                        continue

                    valid_xy_data = [d for d in xyList_pressure if hasattr(d, 'data') and len(d.data) > 0]
                    if not valid_xy_data:
                         print '  WARNING: Los XYData generados para "%s" estan vacios. Saltando.' % elem_set_name
                         for xy in xyList_pressure:
                             if xy.name in session.xyDataObjects.keys():
                                 try: del session.xyDataObjects[xy.name]
                                 except KeyError: pass
                         continue

                    xy_avg_pressure = avg(tuple(valid_xy_data))
                    avg_name_temp = xy_avg_pressure.name
                    avg_name_final = 'Pressure_%s_mean' % elem_set_name

                    try:
                        session.xyDataObjects.changeKey(fromName=avg_name_temp, toName=avg_name_final)
                        xy_avg_pressure = session.xyDataObjects[avg_name_final]
                    except KeyError:
                        if avg_name_temp in session.xyDataObjects.keys():
                             session.xyDataObjects.changeKey(fromName=avg_name_temp, toName=avg_name_final)
                             xy_avg_pressure = session.xyDataObjects[avg_name_final]
                        elif avg_name_final in session.xyDataObjects.keys():
                             xy_avg_pressure = session.xyDataObjects[avg_name_final]
                             print "  INFO: Objeto promedio ya existia como '%s'." % avg_name_final
                        else:
                             print "  ERROR: No se encontro objeto promedio para '%s'." % elem_set_name
                             for xy in valid_xy_data:
                                 if xy.name in session.xyDataObjects.keys():
                                     try: del session.xyDataObjects[xy.name]
                                     except KeyError: pass
                             continue

                    report_filename = os.path.join(odb_report_dir, '%s.rpt' % avg_name_final)
                    session.writeXYReport(
                        fileName=report_filename,
                        xyData=(xy_avg_pressure,),
                        appendMode=OFF
                    )
                    print '  Reporte guardado: %s' % report_filename

                    if avg_name_final in session.xyDataObjects.keys():
                        del session.xyDataObjects[avg_name_final]
                    for xy in valid_xy_data:
                       if xy.name in session.xyDataObjects.keys():
                           try: del session.xyDataObjects[xy.name]
                           except KeyError: pass

                except (OdbError, KeyError, TypeError) as e:
                    print '  ERROR (conocido) extrayendo/procesando Presion para set "%s":' % elem_set_name
                    print '    Tipo: %s' % type(e).__name__
                    print '    Mensaje: %s' % e
                    if 'avg_name_final' in locals() and avg_name_final in session.xyDataObjects.keys():
                        try: del session.xyDataObjects[avg_name_final]
                        except KeyError: pass
                    for xy in xyList_pressure:
                        if xy.name in session.xyDataObjects.keys():
                            try: del session.xyDataObjects[xy.name]
                            except KeyError: pass
                except Exception as e:
                    print '  ERROR (inesperado) procesando Presion para set "%s":' % elem_set_name
                    print '    Tipo: %s' % type(e).__name__
                    print '    Mensaje: %s' % e
                    print traceback.format_exc()


            # --- Procesamiento de Aceleracion ---
            print 'INFO: Procesando Aceleracion...'
            node_set_exists = False
            node_labels = []
            node_set_object = None

            # Comprobar existencia del set de nodos
            node_set_location_msg = ""
            if NODE_SET_ACC in odb.rootAssembly.nodeSets.keys():
                node_set_object = odb.rootAssembly.nodeSets[NODE_SET_ACC]
                node_set_location_msg = "Assembly"
            elif current_instance_name in odb.rootAssembly.instances and NODE_SET_ACC in odb.rootAssembly.instances[current_instance_name].nodeSets.keys():
                 node_set_object = odb.rootAssembly.instances[current_instance_name].nodeSets[NODE_SET_ACC]
                 node_set_location_msg = "Instancia '%s'" % current_instance_name
            else:
                print '  ERROR: NodeSet "%s" no encontrado. No se procesara Aceleracion.' % NODE_SET_ACC

            # --- CORRECCION v9: Manejar OdbMeshNodeArray anidado ---
            if node_set_object is not None:
                print '  INFO: NodeSet "%s" encontrado en %s.' % (NODE_SET_ACC, node_set_location_msg)
                node_labels = []
                nodes_sequence = None
                if hasattr(node_set_object, 'nodes'):
                    nodes_sequence = node_set_object.nodes
                    num_elements_in_sequence = len(nodes_sequence)
                    print '  INFO: La secuencia "nodes" del NodeSet contiene %d elementos.' % num_elements_in_sequence

                    nodes_to_iterate_over = [] # La secuencia final de nodos reales

                    if num_elements_in_sequence == 1 and type(nodes_sequence[0]).__name__ == 'OdbMeshNodeArray':
                        # Caso detectado: la secuencia contiene UN OdbMeshNodeArray
                        print '  INFO: Detectado OdbMeshNodeArray anidado. Usando la secuencia interna.'
                        nodes_to_iterate_over = nodes_sequence[0] # Usar el array interno
                        num_nodes_final = len(nodes_to_iterate_over)
                        print '  INFO: La secuencia interna contiene %d nodos.' % num_nodes_final
                    elif num_elements_in_sequence > 0:
                        # Caso "normal": la secuencia contiene los nodos directamente
                        print '  INFO: Asumiendo que la secuencia "nodes" contiene nodos directamente.'
                        nodes_to_iterate_over = nodes_sequence
                        num_nodes_final = len(nodes_to_iterate_over)
                    else:
                        # Caso: la secuencia 'nodes' esta vacia
                        num_nodes_final = 0
                        print '  WARNING: La secuencia "nodes" esta vacia.'

                    # Intentar obtener labels de la secuencia final de nodos
                    if num_nodes_final > 0:
                        try:
                            for node in nodes_to_iterate_over:
                                if hasattr(node, 'label'):
                                    node_labels.append(node.label)
                                else:
                                    print '      WARNING: Objeto encontrado en la secuencia final sin atributo "label". Tipo: %s' % type(node)

                            if node_labels:
                                node_set_exists = True # Marcar como valido para procesar aceleracion
                            else:
                                print '  WARNING: No se pudieron extraer etiquetas validas de la secuencia final de nodos.'
                        except Exception as e_label:
                             print '  ERROR: Ocurrio un error al obtener etiquetas de nodo de la secuencia final:'
                             print '    %s' % e_label
                             print traceback.format_exc()
                    # else: (No es necesario, si num_nodes_final es 0, node_set_exists sigue False)

                else:
                    print '  WARNING: El objeto NodeSet "%s" no tiene el atributo "nodes".' % NODE_SET_ACC
            # --- Fin correccion v9 ---


            if node_set_exists:
                print '  Extraidos %d labels de nodos del NodeSet "%s".' % (len(node_labels), NODE_SET_ACC)

                # --- Bucle de Componentes A1, A2, A3 (sin cambios internos aqui) ---
                for i, component in enumerate(['A1', 'A2', 'A3']):
                    print '    Procesando Componente: %s' % component
                    xyList_accel_comp = []
                    xyNames_accel_comp_temp = []

                    try:
                        # Bucle sobre labels obtenidos
                        for node_label in node_labels:
                            hist_var_name = '%s: %s PI: %s Node %d in NSET %s' % (
                                ACCEL_VAR_PREFIX, component, current_instance_name, node_label, NODE_SET_ACC)
                            temp_xy_name = 'temp_node_%d_%s_%s' % (node_label, component, odb_name_base)

                            try:
                                # Extraer historial
                                if temp_xy_name in session.xyDataObjects.keys():
                                    del session.xyDataObjects[temp_xy_name]

                                xy_node_accel = xyPlot.XYDataFromHistory(
                                    odb=odb,
                                    outputVariableName=hist_var_name,
                                    steps=(current_step_name, ),
                                    suppressQuery=True,
                                    name=temp_xy_name
                                )

                                if hasattr(xy_node_accel, 'data') and len(xy_node_accel.data) > 0:
                                    xyList_accel_comp.append(xy_node_accel)
                                    xyNames_accel_comp_temp.append(xy_node_accel.name)
                                else:
                                    print '      INFO: Datos vacios para "%s" en Nodo %d. Saltando.' % (component, node_label)
                                    if temp_xy_name in session.xyDataObjects.keys():
                                         try: del session.xyDataObjects[temp_xy_name]
                                         except KeyError: pass

                            except OdbError as e:
                                 print '      WARNING (OdbError): No se pudo extraer "%s" para Nodo %d (Output: "%s"). Saltando.' % (component, node_label, hist_var_name)
                                 print '        Mensaje: %s' % e
                            except TypeError as e:
                                 print '      WARNING (TypeError): No se pudo extraer "%s" para Nodo %d (Output: "%s"). Nombre incorrecto o no existe?. Saltando.' % (component, node_label, hist_var_name)
                            except Exception as e_node:
                                 print '      ERROR (inesperado) extrayendo "%s" para Nodo %d:' % (component, node_label)
                                 print '        Tipo: %s' % type(e_node).__name__
                                 print '        Mensaje: %s' % e_node

                        # Reportes, promedio y limpieza
                        if not xyList_accel_comp:
                            print '    WARNING: No se extrajeron datos validos para %s.' % component
                            continue

                        report_filename_indiv = os.path.join(odb_report_dir, '%s_Acc.rpt' % component)
                        session.writeXYReport(
                            fileName=report_filename_indiv,
                            xyData=tuple(xyList_accel_comp),
                            appendMode=OFF
                        )
                        print '    Reporte individual guardado: %s' % report_filename_indiv

                        xy_avg_accel = avg(tuple(xyList_accel_comp))
                        avg_name_temp = xy_avg_accel.name
                        avg_name_final = '%s_Acc_mean' % component

                        try:
                            session.xyDataObjects.changeKey(fromName=avg_name_temp, toName=avg_name_final)
                            xy_avg_accel = session.xyDataObjects[avg_name_final]
                        except KeyError:
                             if avg_name_temp in session.xyDataObjects.keys():
                                 session.xyDataObjects.changeKey(fromName=avg_name_temp, toName=avg_name_final)
                                 xy_avg_accel = session.xyDataObjects[avg_name_final]
                             elif avg_name_final in session.xyDataObjects.keys():
                                 xy_avg_accel = session.xyDataObjects[avg_name_final]
                                 print "    INFO: Objeto promedio ya existia como '%s'." % avg_name_final
                             else:
                                 print "    ERROR: No se encontro objeto promedio para '%s'." % component
                                 for name in xyNames_accel_comp_temp:
                                     if name in session.xyDataObjects.keys():
                                         try: del session.xyDataObjects[name]
                                         except KeyError: pass
                                 continue

                        report_filename_avg = os.path.join(odb_report_dir, '%s.rpt' % avg_name_final)
                        session.writeXYReport(
                            fileName=report_filename_avg,
                            xyData=(xy_avg_accel,),
                            appendMode=OFF
                        )
                        print '    Reporte promedio guardado: %s' % report_filename_avg

                        if avg_name_final in session.xyDataObjects.keys():
                            del session.xyDataObjects[avg_name_final]

                    except (OdbError, KeyError, TypeError, IOError, OSError) as e:
                        print '    ERROR (conocido) procesando/guardando datos para componente %s:' % component
                        print '      Tipo: %s' % type(e).__name__
                        print '      Mensaje: %s' % e
                    except Exception as e:
                         print '    ERROR (inesperado) procesando componente %s:' % component
                         print '      Tipo: %s' % type(e).__name__
                         print '      Mensaje: %s' % e
                         print traceback.format_exc()

                    finally:
                        print '    Limpiando %d objetos XYData individuales temporales...' % len(xyNames_accel_comp_temp)
                        for name in xyNames_accel_comp_temp:
                            if name in session.xyDataObjects.keys():
                                try: del session.xyDataObjects[name]
                                except KeyError: pass
                                except Exception as e_del:
                                    print '      WARNING: No se pudo borrar XYData "%s": %s' % (name, e_del)
                # --- Fin bucle componentes ---

            # --- Fin del if node_set_exists ---
            else:
                print 'INFO: Saltando procesamiento de aceleracion porque el NodeSet no fue validado.'


        # --- Bloque de Manejo de Errores General para el ODB ---
        except OdbError as e:
            print 'ERROR: Problema especifico de ODB: %s' % odb_file
            print '  %s' % e
        except (KeyError, TypeError) as e:
            print 'ERROR: Error de Scripting (Key/Type): %s' % e
            print '       ODB: %s' % odb_file
            print traceback.format_exc() # Mas detalles
        except (IOError, OSError) as e:
             print 'ERROR: Error de Archivo/Directorio: %s' % e
             print '       ODB: %s' % odb_file
        except Exception as e:
            print 'ERROR: Ocurrio un error inesperado general procesando: %s' % odb_file
            print '  Tipo: %s' % type(e).__name__
            print '  Mensaje: %s' % e
            print traceback.format_exc()

        finally:
            # --- Cerrar ODB ---
            if odb is not None:
                odb_name_in_session = odb.name
                if odb_name_in_session in session.odbs:
                    print 'INFO: Cerrando ODB: %s' % odb_file
                    try:
                        session.odbs[odb_name_in_session].close()
                    except Exception as close_err:
                        print 'WARNING: Problema al cerrar ODB %s: %s' % (odb_file, close_err)
            odb = None

    print '\nINFO: Proceso completado para todos los ODB encontrados.'

# --- Ejecutar la funcion principal ---
if __name__ == '__main__':
    print "INFO: Limpiando XY Plots y XY Data existentes antes de empezar..."
    # ... (limpieza sin cambios) ...
    plot_keys = session.xyPlots.keys()
    for plot_name in plot_keys:
        try: del session.xyPlots[plot_name]
        except Exception as e: print "WARNING: No se pudo borrar XY Plot '%s': %s" % (plot_name, e)

    data_keys = session.xyDataObjects.keys()
    reserved_names = ['Time', 'X', 'Y']
    keys_to_delete = [k for k in data_keys if k not in reserved_names and not k.startswith('__')]
    print "INFO: Intentando borrar %d objetos XYData..." % (len(keys_to_delete))
    deleted_count = 0
    for data_name in keys_to_delete:
         try:
             del session.xyDataObjects[data_name]
             deleted_count += 1
         except Exception as e:
             print "WARNING: No se pudo borrar XY Data '%s': %s" % (data_name, e)
    print "INFO: Limpieza completada (%d objetos XYData borrados)." % (deleted_count)

    process_odb_files()
