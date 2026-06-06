import streamlit as st
import google.generativeai as genai
from datetime import datetime
import os
import pytz  # Movido al inicio para corregir el entorno en la nube

# =====================================================================
# CONFIGURACIÓN DE LA API DE GEMINI (Oculta de forma segura)
# =====================================================================
# Intenta leer desde las variables de entorno de la nube o locales
api_key = os.environ.get("GEMINI_API_KEY")

# Evita el quiebre si st.secrets no está configurado en tu PC local
if not api_key:
    try:
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

if api_key:
    genai.configure(api_key=api_key)
else:
    # Muestra advertencia en local en vez de romper la consola con un crash
    st.warning("Falta la configuración de la API Key de Gemini. En producción, asegúrate de añadirla en Settings > Secrets.")

# Inyección de estilos CSS para mantener tu paleta de colores morados en la Web/PWA
st.markdown(f"""
    <style>
    /* Fondo general oscuro */
    .stApp {{
        background-color: #2B2B2B;
    }}
    /* Botón con tus colores exactos: Morado base y Hover */
    .stButton>button {{
        background-color: #6A1B9A !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        padding: 0.5rem 2rem !important;
    }}
    .stButton>button:hover {{
        background-color: #4A148C !important;
    }}
    /* Estilo para simular las celdas de la tabla visual */
    .celda-cabecera {{
        background-color: #710784;
        color: white;
        padding: 6px 10px;
        border-radius: 4px;
        font-weight: bold;
        margin: 2px;
    }}
    .celda-normal {{
        background-color: #3E1A53;
        color: white;
        padding: 6px 10px;
        border-radius: 4px;
        margin: 2px;
    }}
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# CONFIGURACIÓN DE LA INTERFAZ GRÁFICA (Estructura original)
# =====================================================================
st.title("¿Que tareas tienes?")
st.write(f"Hora actual detectada en el servidor: {datetime.now(pytz.timezone('America/Santiago')).strftime('%H:%M')}")
# Textbox de entrada de texto corregido para accesibilidad
texto_usuario = st.text_area(
    label="Entrada de tareas", 
    label_visibility="collapsed",
    placeholder="Escribe aquí todo lo que tienes que hacer hoy de forma desordenada...",
    height=120
)

# Contenedor para el botón "Optimizar mi Día"
if st.button("Optimizar mi Día"):
    
    # Validación de texto vacío
    if not texto_usuario.strip():
        st.error("Por favor, escribe tus tareas primero.")
    else:
        # Configurar la zona horaria de Chile
        zona_chile = pytz.timezone("America/Santiago")
        hora_actual = datetime.now(zona_chile).strftime("%H:%M")

        prompt = f"""
        Eres un planificador de tareas inmediato. El usuario te dará una lista de actividades y la hora actual.
        Tu único trabajo es asignarles un bloque de tiempo a esas tareas específicas, empezando desde la hora actual hasta el final del día de hoy (máximo 00:00).

        INFORMACIÓN DE CONTEXTO:
        - Hora actual: {hora_actual}. Solo planifica desde esta hora en adelante.

        REGLAS ESTRICTAS:
        1. NO agregues bloques automáticos que el usuario no pidió (como dormir, despertar, desayunar, lavarse los dientes, etc.). 
        2. NO planifiques nada para el día siguiente. El horario debe terminar hoy antes de la medianoche.
        3. Si quedan pocas horas en el día, comprime las tareas solicitadas en el tiempo disponible o distribúyelas de forma realista en lo que queda de jornada.
        4. Formato: Entrega ÚNICAMENTE la tabla Markdown con las columnas [Horas] | [Tarea] | [Notas de Enfoque].
        5. Sé extremadamente breve en las notas. Prohibido agregar introducciones o texto fuera de la tabla.
        4. REGLA DE REDONDEO: Todas las horas de inicio y fin de los bloques DEBEN terminar obligatoriamente
           en números redondos, específicamente múltiplos de 5 o 10 (por ejemplo: 12:20, 12:25, 14:00, 14:35). Evita usar minutos exactos como 12:23 o 14:41.
        Tareas del usuario:
        {texto_usuario}
        """

        generation_config = {
            "temperature": 0.3,
        }

        try:
            model = genai.GenerativeModel("gemini-2.5-flash", generation_config=generation_config)
            response = model.generate_content(prompt)
            
            st.write("### Plan de Enfo:")
            
            # Procesar el texto Markdown para extraer las filas y pasarlas a la Grid Web
            lineas = response.text.strip().split("\n")
            
            # Contenedor con scroll simulado para la tabla
            with st.container():
                for linea in lineas:
                    if not linea.strip() or "---" in linea:
                        continue
                    
                    columnas = [col.strip() for col in linea.split("|") if col.strip()]
                    
                    if len(columnas) >= 3:
                        # Crear las 3 columnas con la proporción original (weight 1, 2, 3)
                        col1, col2, col3 = st.columns([1, 2, 3])
                        cols_layout = [col1, col2, col3]
                        
                        for col_idx, texto in enumerate(columnas[:3]):
                            es_cabecera = "Horas" in columnas[0] or "Tarea" in columnas[1]
                            clase_celda = "celda-cabecera" if es_cabecera else "celda-normal"
                            
                            # Dibujar la celda en la columna correspondiente manteniendo el color asignado
                            cols_layout[col_idx].markdown(
                                f'<div class="{clase_celda}">{texto}</div>', 
                                unsafe_allow_html=True
                            )
        except Exception as e:
            st.error(f"Error al conectar con la IA: {e}")

