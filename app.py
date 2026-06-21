import streamlit as st
import cv2
import mysql.connector
import numpy as np
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Sistema UPSJB", layout="wide")

CARPETA_ROSTROS = "Rostros"
if not os.path.exists(CARPETA_ROSTROS):
    os.makedirs(CARPETA_ROSTROS)

def conectar_db():
    return mysql.connector.connect(
        host="bevdnvgkkduta9w5ixbk-mysql.services.clever-cloud.com",
        user="ukgd0acstccmz2k9",
        password="Q7yj6LmjeFhjiZ7IwiHP",
        database="bevdnvgkkduta9w5ixbk",
        port=3306
    )

st.sidebar.image("logo.jpg", use_column_width=True)
st.sidebar.title("MENÚ PRINCIPAL")
opcion = st.sidebar.radio("", ["Marcación de Asistencia", "Registro de Alumno", "Reportes Académicos"])
st.sidebar.markdown("---")
st.sidebar.markdown("**SISTEMA UPSJB**")

if opcion == "Marcación de Asistencia":
    st.title("📸 Marcación de Asistencia Biométrica")
    st.subheader("Colóquese frente a la cámara para registrar su entrada")
    
    img_file = st.camera_input("Asigne su rostro en el recuadro")
    
    if img_file is not None:
        alumnos_existentes = [os.path.splitext(f)[0] for f in os.listdir(CARPETA_ROSTROS) if f.endswith(('.jpg', '.png'))]
        
        if alumnos_existentes:
            alumno_detectado = st.selectbox("Seleccione el alumno detectado (Simulación AI)", alumnos_existentes)
            
            if st.button("Confirmar Asistencia"):
                try:
                    conn = conectar_db()
                    cursor = conn.cursor()
                    
                    fecha_actual = datetime.now().strftime("%Y-%m-%d")
                    query_check = "SELECT * FROM asistencia WHERE nombre = %s AND fecha_hora LIKE %s"
                    cursor.execute(query_check, (alumno_detectado, f"{fecha_actual}%"))
                    
                    if cursor.fetchone():
                        st.warning(f"⚠️ {alumno_detectado} ya registró su asistencia el día de hoy.")
                    else:
                        query_insert = "INSERT INTO asistencia (nombre, fecha_hora) VALUES (%s, %s)"
                        cursor.execute(query_insert, (alumno_detectado, datetime.now()))
                        conn.commit()
                        st.success(f"✅ Asistencia registrada exitosamente para: {alumno_detectado}")
                        
                    cursor.close()
                    conn.close()
                except Exception as e:
                    st.error(f"Error de base de datos: {e}")
        else:
            st.info("No hay alumnos registrados en el sistema todavía.")

elif opcion == "Registro de Alumno":
    st.title("👤 Panel de Gestión de Estudiantes (CRUD)")
    
    tab1, tab2, tab3 = st.tabs(["🆕 Registrar Nuevo Alumno", "✏️ Editar Nombres / Apellidos", "❌ Eliminar Alumno"])
    
    with tab1:
        st.header("Registrar Nuevo Estudiante")
        nuevo_nombre = st.text_input("Escriba Nombre y Apellidos del Alumno:")
        
        foto_alumno = st.camera_input("Capture el rostro del alumno para el registro:")
        
        if st.button("Guardar Registro"):
            if nuevo_nombre and foto_alumno:
                nombre_limpio = nuevo_nombre.strip().replace(" ", "_")
                ruta_foto = os.path.join(CARPETA_ROSTROS, f"{nombre_limpio}.jpg")
                
                with open(ruta_foto, "wb") as f:
                    f.write(foto_alumno.getbuffer())
                st.success(f"🎉 Alumno '{nuevo_nombre}' guardado correctamente.")
                st.rerun()
            else:
                st.error("Por favor, ingrese el nombre y capture la fotografía con la cámara.")
                
    with tab2:
        st.header("Editar Información del Alumno")
        alumnos_existentes = [os.path.splitext(f)[0].replace("_", " ") for f in os.listdir(CARPETA_ROSTROS) if f.endswith(('.jpg', '.png'))]
        
        if alumnos_existentes:
            alumno_a_editar = st.selectbox("Seleccione el alumno que desea corregir:", alumnos_existentes)
            nuevo_nombre_editado = st.text_input("Escriba el nombre corregido (con apellidos):", value=alumno_a_editar)
            
            if st.button("Actualizar Nombre del Alumno"):
                if nuevo_nombre_editado.strip() != "":
                    old_filename = alumno_a_editar.replace(" ", "_")
                    new_filename = nuevo_nombre_editado.strip().replace(" ", "_")
                    
                    old_path = os.path.join(CARPETA_ROSTROS, f"{old_filename}.jpg")
                    new_path = os.path.join(CARPETA_ROSTROS, f"{new_filename}.jpg")
                    
                    if os.path.exists(old_path):
                        os.rename(old_path, new_path)
                    
                    try:
                        conn = conectar_db()
                        cursor = conn.cursor()
                        query_update = "UPDATE asistencia SET nombre = %s WHERE nombre = %s"
                        cursor.execute(query_update, (nuevo_nombre_editado.strip(), alumno_a_editar))
                        conn.commit()
                        cursor.close()
                        conn.close()
                        st.success(f"🔄 Se actualizó de '{alumno_a_editar}' a '{nuevo_nombre_editado.strip()}'.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al actualizar la base de datos: {e}")
        else:
            st.info("No hay alumnos para editar.")

    with tab3:
        st.header("Eliminar Alumno del Sistema")
        alumnos_existentes_del = [os.path.splitext(f)[0].replace("_", " ") for f in os.listdir(CARPETA_ROSTROS) if f.endswith(('.jpg', '.png'))]
        
        if alumnos_existentes_del:
            alumno_a_eliminar = st.selectbox("Seleccione el alumno que desea dar de baja:", alumnos_existentes_del)
            st.warning(f"⚠️ Al eliminar a **{alumno_a_eliminar}** se borrará su fotografía y todo su historial de asistencias de forma permanente.")
            
            if st.button("🔴 Confirmar Eliminación Definitiva"):
                filename_to_del = alumno_a_eliminar.replace(" ", "_")
                path_to_del = os.path.join(CARPETA_ROSTROS, f"{filename_to_del}.jpg")
                
                if os.path.exists(path_to_del):
                    os.remove(path_to_del)
                
                try:
                    conn = conectar_db()
                    cursor = conn.cursor()
                    query_delete = "DELETE FROM asistencia WHERE nombre = %s"
                    cursor.execute(query_delete, (alumno_a_eliminar,))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    st.success(f"❌ El alumno '{alumno_a_eliminar}' y su historial han sido eliminados.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al eliminar de la base de datos: {e}")
        else:
            st.info("No hay alumnos registrados para eliminar.")

elif opcion == "Reportes Académicos":
    st.title("📊 Historial de Asistencia Estudiantil")
    
    try:
        conn = conectar_db()
        query = "SELECT id as 'ID', nombre as 'Estudiante', fecha_hora as 'Fecha y Hora' FROM asistencia ORDER BY fecha_hora DESC"
        df = pd.read_sql(query, conn)
        conn.close()
        
        if not df.empty:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Total Registros", len(df))
            with c2:
                hoy = datetime.now().strftime("%Y-%m-%d")
                df['Fecha_Str'] = df['Fecha y Hora'].astype(str)
                total_hoy = df[df['Fecha_Str'].str.contains(hoy)].shape[0]
                st.metric("Hoy", total_hoy)
            with c3:
                st.metric("Alumnos Únicos", df['Estudiante'].nunique())
                
            st.markdown("---")
            st.dataframe(df[['ID', 'Estudiante', 'Fecha y Hora']], use_container_width=True)
            
            st.subheader("Estadística por Alumno")
            conteo_asistencias = df['Estudiante'].value_counts()
            st.bar_chart(conteo_asistencias)
        else:
            st.info("📅 Aún no se registran asistencias en la base de datos.")
    except Exception as e:
        st.error(f"Error al conectar con los reportes: {e}")
