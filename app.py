import streamlit as st
import cv2
import numpy as np
import mysql.connector
import os
import pandas as pd
from datetime import datetime

CARPETA_ROSTROS = "Rostros"
if not os.path.exists(CARPETA_ROSTROS):
    os.makedirs(CARPETA_ROSTROS)

st.set_page_config(page_title="UPSJB - Sistema Biométrico", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    /* Estilos dinámicos adaptables al modo claro y oscuro */
    [data-testid="stMetricValue"] { 
        color: #0284c7 !important; 
        font-weight: bold; 
    }
    
    /* Botón estándar (Rojo UPSJB para asistencia) */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3.5em;
        background-color: #cc0000;
        color: white !important;
        font-weight: bold;
        border: none;
        transition: background-color 0.3s;
    }
    .stButton>button:hover { 
        background-color: #a30000; 
        color: white !important; 
    }
    
    /* Contenedor específico para el botón de guardar en color azul */
    .blue-btn .stButton>button {
        background-color: #2563eb !important;
        color: white !important;
    }
    .blue-btn .stButton>button:hover {
        background-color: #1d4ed8 !important;
        color: white !important;
    }
    
    /* Mejoras en la barra lateral */
    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(128, 128, 128, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)

def conectar_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="admin123",
        database="asistencia"
    )

def registrar_asistencia_db(nombre):
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        fecha_hoy = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("SELECT * FROM asistencia WHERE nombre=%s AND fecha_hora LIKE %s", (nombre, f"{fecha_hoy}%"))
        if cursor.fetchone() is None:
            ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("INSERT INTO asistencia (nombre, fecha_hora) VALUES (%s, %s)", (nombre, ahora))
            conn.commit()
            cursor.close()
            conn.close()
            return True, f"Bienvenido(a), {nombre}."
        cursor.close()
        conn.close()
        return False, "Ya registraste tu asistencia hoy."
    except:
        return False, "Error de conexión con el servidor."

def entrenar_reconocedor():
    reconocedor = cv2.face.LBPHFaceRecognizer_create()
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    rostros, ids, mapa_nombres = [], [], {}
    archivos = [f for f in os.listdir(CARPETA_ROSTROS) if f.endswith(('.jpg', '.jpeg', '.png'))]
    if not archivos: return None, {}
    for idx, archivo in enumerate(archivos):
        img = cv2.imread(os.path.join(CARPETA_ROSTROS, archivo), cv2.IMREAD_GRAYSCALE)
        mapa_nombres[idx] = os.path.splitext(archivo)[0].replace("_", " ")
        faces = detector.detectMultiScale(img, 1.3, 5)
        for (x, y, w, h) in faces:
            rostros.append(img[y:y+h, x:x+w])
            ids.append(idx)
    if not rostros: return None, {}
    reconocedor.train(rostros, np.array(ids))
    return reconocedor, mapa_nombres

with st.sidebar:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", use_container_width=True)
    else:
        st.image("https://www.upsjb.edu.pe/wp-content/uploads/2021/11/logo-upsjb-1.png", use_container_width=True)
    st.divider()
    opcion = st.sidebar.radio("MENÚ PRINCIPAL", ["Marcación de Asistencia", "Registro de Alumno", "Reportes Académicos"])
    st.divider()
    st.write("**SISTEMA UPSJB v2.5**")

if opcion == "Marcación de Asistencia":
    st.header("🎓 Control de Asistencia Facial")
    st.write("Colóquese frente a la cámara para validar su identidad académica.")
    
    img_buffer = st.camera_input("Tomar foto para registrar asistencia")

    if img_buffer:
        img = cv2.imdecode(np.frombuffer(img_buffer.getvalue(), np.uint8), cv2.IMREAD_COLOR)
        gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = detector.detectMultiScale(gris, 1.3, 5)
        
        if len(faces) > 0:
            rec, mapa = entrenar_reconocedor()
            if rec:
                for (x, y, w, h) in faces:
                    idx, conf = rec.predict(gris[y:y+h, x:x+w])
                    if conf < 70:
                        exito, msg = registrar_asistencia_db(mapa[idx])
                        if exito: st.success(f"✅ {msg}")
                        else: st.info(msg)
                    else:
                        st.error("❌ Estudiante no reconocido.")
            else:
                st.warning("No hay alumnos registrados.")
        else:
            st.error("No se detectó ningún rostro.")

elif opcion == "Registro de Alumno":
    st.header("👤 Registro de Nuevo Estudiante")
    nombre = st.text_input("Ingrese Nombres y Apellidos Completos:")
    foto = st.file_uploader("Subir foto frontal nítida", type=["jpg", "png", "jpeg"])
    
    # Envolver el botón en un contenedor con clase para aplicar estilo azul
    st.markdown('<div class="blue-btn">', unsafe_allow_html=True)
    guardar_btn = st.button("Guardar Datos del Estudiante")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if guardar_btn:
        if nombre and foto:
            nombre_file = nombre.strip().replace(" ", "_") + ".jpg"
            with open(os.path.join(CARPETA_ROSTROS, nombre_file), "wb") as f:
                f.write(foto.getbuffer())
            st.success(f"¡Registro completado para {nombre}!")
            st.balloons()
        else:
            st.error("Por favor, completa el nombre y sube una foto.")

elif opcion == "Reportes Académicos":
    st.header("📊 Historial de Asistencia Estudiantil")
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id as ID, nombre as Estudiante, fecha_hora as 'Fecha y Hora' FROM asistencia ORDER BY fecha_hora DESC")
        res = cursor.fetchall()
        
        if res:
            df = pd.DataFrame(res, columns=['ID', 'Estudiante', 'Fecha y Hora'])
            df['Fecha y Hora'] = pd.to_datetime(df['Fecha y Hora'])
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Registros", len(df))
            c2.metric("Hoy", len(df[df['Fecha y Hora'].dt.date == datetime.now().date()]))
            c3.metric("Alumnos Únicos", df['Estudiante'].nunique())
            
            st.divider()
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.subheader("Estadística por Alumno")
            st.bar_chart(df['Estudiante'].value_counts())
        else:
            st.info("Aún no hay asistencias registradas.")
        
        cursor.close()
        conn.close()
    except Exception as e:
        st.error(f"Error de base de datos: {e}")