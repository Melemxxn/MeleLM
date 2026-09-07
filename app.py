import streamlit as st
import PyPDF2
import docx
import google.generativeai as genai
import json
import uuid
import time
import urllib.parse
import requests
from datetime import datetime, timezone

# ==========================================
# 1. Configuración inicial de la página
# ==========================================
st.set_page_config(
    page_title="MeleLM",
    page_icon="📚",
    layout="centered"
)

import firebase_admin
from firebase_admin import credentials, firestore

# ==========================================
# 2. Autenticación Google OAuth & Gatekeeper (Nativo con requests & urllib)
# ==========================================
client_id = st.secrets["google_oauth"]["client_id"]
client_secret = st.secrets["google_oauth"]["client_secret"]
redirect_uri = st.secrets["google_oauth"]["redirect_uri"]

# Manejar el callback de Google OAuth mediante query_params
if "user_email" not in st.session_state:
    code = st.query_params.get("code")
    if code:
        try:
            token_url = "https://oauth2.googleapis.com/token"
            data = {
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code"
            }
            token_res = requests.post(token_url, data=data)
            token_data = token_res.json()
            access_token = token_data.get("access_token")

            if access_token:
                user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
                headers = {"Authorization": f"Bearer {access_token}"}
                user_res = requests.get(user_info_url, headers=headers)
                user_info = user_res.json()
                email = user_info.get("email")

                if email:
                    st.session_state["user_email"] = email
                    st.session_state["user_id"] = email
                    st.query_params.clear()
                    st.rerun()
                else:
                    st.error("No se pudo obtener el correo electrónico del usuario.")
            else:
                st.error("No se pudo obtener el token de acceso de Google.")
        except Exception as e:
            st.error(f"⚠️ Error durante la autenticación nativa con Google: {e}")

if "user_email" not in st.session_state:
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account"
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"

    st.markdown(
        f"""
        <style>
        /* Ocultar barra lateral, header y footer por defecto en la pantalla de login */
        [data-testid="stSidebar"] {{ display: none !important; }}
        header {{ visibility: hidden !important; }}
        footer {{ visibility: hidden !important; }}
        
        /* Fondo general oscuro */
        .stApp {{
            background: linear-gradient(135deg, #0d1117 0%, #161b22 100%) !important;
        }}

        /* Contenedor wrapper centrado */
        .login-wrapper {{
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 80vh;
            padding: 1rem;
        }}

        /* Tarjeta modal ALMA Dark UI */
        .login-card {{
            width: 100%;
            max-width: 400px;
            background: #161b22;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 24px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
            padding: 2.5rem 2rem;
            text-align: center;
            margin: 0 auto;
        }}

        /* Isotipo / Avatar circular superior */
        .login-logo-circle {{
            width: 64px;
            height: 64px;
            margin: 0 auto 1.25rem auto;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            font-weight: 700;
            color: #ffffff;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }}

        /* Título principal y subtítulo */
        .login-title {{
            font-size: 1.5rem;
            font-weight: 700;
            color: #ffffff;
            margin: 0 0 0.25rem 0;
            letter-spacing: -0.3px;
        }}

        .login-subtitle {{
            font-size: 0.7rem;
            font-weight: 600;
            letter-spacing: 1.5px;
            color: #8b949e;
            text-transform: uppercase;
            margin-bottom: 1.5rem;
        }}

        /* Divisor elegante */
        .login-divider {{
            display: flex;
            align-items: center;
            text-align: center;
            margin: 1.5rem 0;
            color: #6e7681;
            font-size: 0.68rem;
            font-weight: 600;
            letter-spacing: 1px;
            text-transform: uppercase;
        }}

        .login-divider::before, .login-divider::after {{
            content: '';
            flex: 1;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }}

        .login-divider:not(:empty)::before {{
            margin-right: .75em;
        }}

        .login-divider:not(:empty)::after {{
            margin-left: .75em;
        }}

        /* Botón de Google nativo HTML <a> sin iframe */
        .google-login-btn {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            width: 100%;
            background-color: #21262d;
            color: #ffffff !important;
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 12px;
            padding: 0.85rem 1.25rem;
            font-weight: 600;
            font-size: 0.95rem;
            text-decoration: none !important;
            transition: all 0.2s ease-in-out;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            box-sizing: border-box;
        }}

        .google-login-btn:hover {{
            background-color: #30363d;
            border-color: rgba(255, 255, 255, 0.3);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
            color: #ffffff !important;
            text-decoration: none !important;
        }}

        .google-icon {{
            width: 18px;
            height: 18px;
            flex-shrink: 0;
        }}

        /* Pie de tarjeta */
        .login-footer-note {{
            font-size: 0.75rem;
            color: #6e7681;
            margin-top: 1.5rem;
            line-height: 1.4;
        }}
        </style>

        <div class="login-wrapper">
            <div class="login-card">
                <div class="login-logo-circle">M</div>
                <h2 class="login-title">MeleLM</h2>
                <div class="login-subtitle">ANÁLISIS INTELIGENTE DE DOCUMENTOS</div>
                <div class="login-divider">ACCEDER CON TU CUENTA</div>
                <a href="{auth_url}" target="_top" class="google-login-btn">
                    <svg class="google-icon" viewBox="0 0 24 24">
                        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
                    </svg>
                    <span>Continuar con Google</span>
                </a>
                <p class="login-footer-note">Tus documentos se procesan de forma privada</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.stop()

# ==========================================
# Base de Datos (Firebase Firestore)
# ==========================================
def init_firebase():
    """
    Inicializa Firebase Admin SDK usando credenciales de st.secrets['firebase'].
    Devuelve el cliente de Firestore.
    """
    if not firebase_admin._apps:
        try:
            firebase_config = dict(st.secrets["firebase"])
            cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"⚠️ Error al inicializar Firebase: {e}")
            st.stop()
    return firestore.client()

db = init_firebase()

def save_session_to_db():
    """
    Guarda o actualiza el estado de la sesión actual en Firebase Firestore.
    """
    session_id = st.session_state.get("session_id")
    if not session_id:
        return

    historial_json = json.dumps(st.session_state.get("chat_history", []))
    titulo = st.session_state.get("session_title", "Documento sin título")
    pdf_text = st.session_state.get("pdf_text", "")
    resumen = st.session_state.get("resumen_generado", "")
    glossary = st.session_state.get("glossary", "")
    study_guide = st.session_state.get("study_guide", "")
    guion = st.session_state.get("guion_generado", "")
    user_id = st.session_state.get("user_id")

    session_doc = {
        "id": session_id,
        "user_id": user_id,
        "titulo": titulo,
        "pdf_text": pdf_text,
        "historial_chat": historial_json,
        "resumen": resumen,
        "glossary": glossary,
        "study_guide": study_guide,
        "guion": guion,
        "fecha": firestore.SERVER_TIMESTAMP
    }

    try:
        db.collection("sesiones").document(session_id).set(session_doc, merge=True)
    except Exception as e:
        st.error(f"⚠️ Error al guardar sesión en Firestore: {e}")

def get_all_sessions():
    """
    Obtiene todas las sesiones guardadas del usuario actual ordenadas por fecha descendente.
    """
    user_id = st.session_state.get("user_id")
    try:
        docs = (
            db.collection("sesiones")
            .where("user_id", "==", user_id)
            .order_by("fecha", direction=firestore.Query.DESCENDING)
            .stream()
        )
        sessions = []
        for doc in docs:
            d = doc.to_dict()
            sessions.append((d.get("id"), d.get("titulo"), d.get("fecha")))
        return sessions
    except Exception as e:
        # Si falta índice compuesto en Firestore, intentar sin order_by o manejar error
        try:
            docs = db.collection("sesiones").where("user_id", "==", user_id).stream()
            sessions = []
            for doc in docs:
                d = doc.to_dict()
                sessions.append((d.get("id"), d.get("titulo"), d.get("fecha")))
            sessions.sort(key=lambda x: x[2] if x[2] is not None else datetime.min, reverse=True)
            return sessions
        except Exception as inner_e:
            st.error(f"⚠️ Error al consultar sesiones en Firestore: {inner_e}")
            return []

def load_session_from_db(session_id):
    """
    Carga los datos de una sesión almacenada en Firestore hacia st.session_state.
    """
    try:
        doc_ref = db.collection("sesiones").document(session_id)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            st.session_state["session_id"] = data.get("id", session_id)
            st.session_state["session_title"] = data.get("titulo", "Documento sin título")
            st.session_state["pdf_text"] = data.get("pdf_text", "")
            st.session_state["resumen_generado"] = data.get("resumen", "")
            st.session_state["glossary"] = data.get("glossary", "")
            st.session_state["study_guide"] = data.get("study_guide", "")
            st.session_state["guion_generado"] = data.get("guion", "")
            historial_json = data.get("historial_chat", "[]")
            try:
                st.session_state["chat_history"] = json.loads(historial_json) if historial_json else []
            except Exception:
                st.session_state["chat_history"] = []
            
            pdf_text = st.session_state.get("pdf_text", "")
            st.session_state["pdf_metadata"] = {
                "pages": 1 if pdf_text else 0,
                "chars": len(pdf_text)
            }
    except Exception as e:
        st.error(f"⚠️ Error al cargar sesión desde Firestore: {e}")

def start_new_session():
    """
    Reinicia el session_state e inicia un nuevo ID de sesión sin consumo de API.
    """
    st.session_state["session_id"] = str(uuid.uuid4())
    st.session_state["session_title"] = f"Doc - {datetime.now().strftime('%H:%M')}"
    st.session_state["pdf_text"] = ""
    st.session_state["pdf_metadata"] = {"pages": 0, "chars": 0}
    st.session_state["resumen_generado"] = ""
    st.session_state["glossary"] = ""
    st.session_state["study_guide"] = ""
    st.session_state["guion_generado"] = ""
    st.session_state["chat_history"] = []
    st.session_state["ocupado"] = False

# ==========================================
# Configuración segura de la API Key de Google Gemini mediante st.secrets
# ==========================================
def init_gemini_api():
    """
    Lee y configura la API Key desde los secretos de Streamlit (st.secrets["GEMINI_API_KEY"]).
    Instancia directamente la versión del modelo 'gemini-3.6-flash'.
    """
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        st.session_state["model"] = "gemini-3.6-flash"
        return True
    except KeyError:
        st.error(
            "⚠️ No se ha encontrado la clave 'GEMINI_API_KEY' en los secretos de Streamlit (`.streamlit/secrets.toml`). "
            "Por favor, añade la clave para continuar."
        )
        return False
    except Exception as e:
        st.error(f"⚠️ Error al configurar la API Key de Google Gemini: {e}")
        return False

# ==========================================
# Funciones cacheadas con @st.cache_data para extracción de texto y API
# ==========================================
@st.cache_data(show_spinner=False)
def extract_text_from_pdfs(archivos_subidos):
    """
    Extrae y combina el texto de una lista de archivos (.pdf, .docx, .txt).
    Devuelve la tupla (texto_combinado, total_paginas).
    """
    texto_combinado = ""
    total_paginas = 0

    for archivo in archivos_subidos:
        nombre = archivo.name.lower()
        if nombre.endswith(".pdf"):
            try:
                reader = PyPDF2.PdfReader(archivo)
                total_paginas += len(reader.pages)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        texto_combinado += text + "\n"
            except Exception as e:
                st.error(f"Error al leer el archivo PDF {archivo.name}: {e}")
        elif nombre.endswith(".docx"):
            try:
                doc = docx.Document(archivo)
                total_paginas += 1
                for paragraph in doc.paragraphs:
                    if paragraph.text:
                        texto_combinado += paragraph.text + "\n"
            except Exception as e:
                st.error(f"Error al leer el archivo DOCX {archivo.name}: {e}")
        elif nombre.endswith(".txt"):
            try:
                content = archivo.read().decode("utf-8")
                total_paginas += 1
                texto_combinado += content + "\n"
            except Exception as e:
                st.error(f"Error al leer el archivo TXT {archivo.name}: {e}")

    return texto_combinado, total_paginas

@st.cache_data(show_spinner=False)
def generar_resumen_api(texto_reducido):
    """
    Genera el resumen llamando directamente a la API de Gemini usando 'gemini-3.6-flash'.
    Resultados almacenados en la caché de Streamlit según el contenido del texto.
    """
    model = genai.GenerativeModel("gemini-3.6-flash")
    prompt = f"""
    Actúa como un asistente de investigación experto. A continuación se te proporciona el texto extraído de un documento.
    Genera un resumen estructurado con viñetas destacando los puntos principales, conceptos clave y conclusiones del documento.
    
    REGLA IMPRESCINDIBLE: Basa tu respuesta EXCLUSIVAMENTE en el texto proporcionado. No añadas información externa ni asunciones.

    Texto del documento:
    \"\"\"
    {texto_reducido}
    \"\"\"
    """
    response = model.generate_content(prompt)
    return response.text

@st.cache_data(show_spinner=False)
def generar_podcast_api(texto_reducido):
    """
    Genera el guion del podcast llamando directamente a la API de Gemini usando 'gemini-3.6-flash'.
    Resultados almacenados en la caché de Streamlit según el contenido del texto.
    """
    model = genai.GenerativeModel("gemini-3.6-flash")
    prompt = f"""
    Basándote en este documento, genera un guion de un podcast donde dos presentadores (por ejemplo, Alex y Laura) discuten, explican y debaten los puntos clave del texto de forma amena, natural y divulgativa.
    Genera un guion CORTO, de unos 2-3 minutos de duración.
    
    El guion debe incluir:
    - Una introducción atractiva de bienvenida al episodio.
    - Diálogos fluidos entre Alex y Laura alternando explicaciones, preguntas y comentarios interesantes.
    - Una conclusión recapitulando los aprendizajes principales del texto.

    Texto del documento:
    \"\"\"
    {texto_reducido}
    \"\"\"
    """
    response = model.generate_content(prompt)
    return response.text

# ==========================================
# Funciones adicionales (Glosario, Guía y Chat)
# ==========================================
def generate_glossary(text):
    model_name = st.session_state.get("model", "models/gemini-1.5-flash")
    model = genai.GenerativeModel(model_name)
    texto_recortado = text[:30000]
    prompt = f"""
    Actúa como un profesor o investigador experto. A partir del texto proporcionado del documento,
    extrae los 10 conceptos o términos más importantes y define brevemente cada uno de ellos.
    
    REGLA IMPRESCINDIBLE: Basa tus definiciones EXCLUSIVAMENTE en la información del texto proporcionado.

    Texto del documento:
    \"\"\"
    {texto_recortado}
    \"\"\"
    """
    response = model.generate_content(prompt)
    return response.text

def generate_study_guide(text):
    model_name = st.session_state.get("model", "models/gemini-1.5-flash")
    model = genai.GenerativeModel(model_name)
    texto_recortado = text[:30000]
    prompt = f"""
    Actúa como un diseñador instruccional experto. A partir del texto proporcionado del documento, genera una Guía de Estudio que incluya:
    1. 5 Preguntas de desarrollo con su correspondiente respuesta explicativa basada en el texto.
    2. 5 Preguntas de opción múltiple (tipo test con opciones A, B, C, D) indicando las respuestas correctas al final de la sección.

    REGLA IMPRESCINDIBLE: Toda la guía de estudio debe estar basada EXCLUSIVAMENTE en el contenido del documento.

    Texto del documento:
    \"\"\"
    {texto_recortado}
    \"\"\"
    """
    response = model.generate_content(prompt)
    return response.text

def answer_chat_question(text, chat_history, question):
    model_name = st.session_state.get("model", "models/gemini-1.5-flash")
    model = genai.GenerativeModel(model_name)
    texto_recortado = text[:30000]
    formatted_history = ""
    for msg in chat_history[-6:]:
        role_label = "Usuario" if msg["role"] == "user" else "Asistente"
        formatted_history += f"{role_label}: {msg['content']}\n"

    prompt = f"""
    Actúa como un **investigador académico riguroso** y experto en análisis documental.
    Tu objetivo es responder a la pregunta del usuario basándote ÚNICA Y EXCLUSIVAMENTE en el texto del documento proporcionado.

    REGLAS DE RESPUESTA:
    1. **Respaldo con citas literales**: Por cada afirmación importante o conclusión que hagas en tu respuesta, DEBES incluir una breve cita literal del documento original entre comillas y en cursiva (ejemplo: *"..."*).
    2. **Sección de referencias**: Al final de tu respuesta, añade una sección titulada '### 📌 Referencias extraídas' donde enumeres las citas o fragmentos textuales exactos utilizados para construir tu respuesta.
    3. **Sin suposiciones ni fuentes externas**: No inventes información ni recurras a conocimientos fuera del documento.
    4. **Ausencia de información**: Si la respuesta a la pregunta no se encuentra explícitamente en el texto del documento, debes indicar con absoluta claridad:
       "La información solicitada no se encuentra en el documento proporcionado."

    Contexto del Documento:
    \"\"\"
    {texto_recortado}
    \"\"\"

    Historial de la conversación reciente:
    {formatted_history}

    Pregunta del usuario:
    {question}
    """
    response = model.generate_content(prompt)
    return response.text

# ==========================================
# Sidebar (Barra Lateral - Historial tipo ChatGPT)
# ==========================================
with st.sidebar:
    st.title("📚 MeleLM")
    
    # Badge con información del usuario autenticado y botón de cierre de sesión
    user_email = st.session_state.get("user_email", "")
    st.markdown(f"👤 **{user_email}**")
    if st.button("🚪 Cerrar sesión", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    st.divider()

    if st.button("➕ Nuevo Documento", use_container_width=True, type="primary"):
        start_new_session()
        st.rerun()

    st.divider()
    st.subheader("🕒 Historial de Sesiones")

    saved_sessions = get_all_sessions()
    if saved_sessions:
        for s_id, title, date_str in saved_sessions:
            display_title = title if title else "Documento sin título"
            button_type = "primary" if s_id == st.session_state.get("session_id") else "secondary"
            if st.button(f"📄 {display_title[:25]}", key=f"session_{s_id}", use_container_width=True, type=button_type):
                load_session_from_db(s_id)
                st.rerun()
    else:
        st.caption("No hay sesiones guardadas todavía.")

    if st.session_state.get("model"):
        st.divider()
        st.caption(f"🤖 Modelo activo: `{st.session_state['model']}`")

# ==========================================
# Área Principal - Interfaz SaaS de la Aplicación
# ==========================================
st.markdown(
    """
    <div class="titulo-container">
        <h1 class="titulo-mele">MeleLM</h1>
        <p class="subtitulo-mele">Tu asistente inteligente para análisis de documentos</p>
    </div>
    """,
    unsafe_allow_html=True
)

api_ready = init_gemini_api()

# Agrupar zona de carga en st.container()
with st.container():
    st.markdown("### 📄 Sube tus apuntes o documentos (PDF, DOCX, TXT)")
    uploaded_files = st.file_uploader(
        label="Selecciona tus archivos",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        help="Formatos permitidos: .pdf, .docx, .txt"
    )

st.divider()

# Procesamiento y lectura de archivos
if uploaded_files:
    st.subheader("📄 Documentos cargados")
    for file in uploaded_files:
        st.write(f"- **{file.name}** ({round(file.size / 1024, 2)} KB)")

    if st.button("Procesar y extraer texto", type="primary"):
        with st.spinner("Extrayendo texto de los archivos cargados..."):
            extracted_text, total_pages = extract_text_from_pdfs(uploaded_files)
            
            if extracted_text is not None and len(extracted_text.strip()) > 0:
                st.session_state["pdf_text"] = extracted_text
                st.session_state["resumen_generado"] = ""
                st.session_state["glossary"] = ""
                st.session_state["study_guide"] = ""
                st.session_state["guion_generado"] = ""
                st.session_state["chat_history"] = []
                st.session_state["pdf_metadata"] = {
                    "pages": total_pages,
                    "chars": len(extracted_text)
                }
                st.session_state["session_title"] = f"Doc - {datetime.now().strftime('%H:%M')}"
                
                # Guardar sesión en Firestore asociada al usuario actual
                save_session_to_db()
                st.rerun()
            else:
                st.session_state["pdf_text"] = ""

# Mostrar vista de la sesión activa (cargada o recién procesada)
if st.session_state.get("pdf_text"):
    st.subheader(f"📌 Sesión Activa: {st.session_state.get('session_title', 'Documento')}")
    st.success(
        f"✅ ¡Texto listo! "
        f"Procesadas **{st.session_state['pdf_metadata']['pages']}** páginas/secciones y "
        f"**{st.session_state['pdf_metadata']['chars']}** caracteres."
    )
    
    with st.expander("Ver vista previa del texto extraído"):
        st.text_area("Texto extraído:", value=st.session_state["pdf_text"][:2000] + "...", height=150, disabled=True)

    st.divider()

    # ==========================================
    # Sección de Generación de Artefactos (Botones en Columnas)
    # ==========================================
    st.subheader("🛠️ Herramientas de Estudio y Divulgación")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📝 Generar Resumen", type="primary", use_container_width=True):
            if not api_ready:
                st.error("⚠️ La API de Gemini no está configurada correctamente en los secretos.")
            else:
                try:
                    with st.spinner("📝 Generando resumen..."):
                        texto_reducido = st.session_state["pdf_text"][:30000]
                        result = generar_resumen_api(texto_reducido)
                        if result:
                            st.session_state["resumen_generado"] = result
                            save_session_to_db()
                            st.rerun()
                except Exception as e:
                    st.error(f"Error interno capturado: {e}")

    with col2:
        if st.button("📖 Generar Glosario", type="secondary", use_container_width=True):
            if not api_ready:
                st.error("⚠️ La API de Gemini no está configurada correctamente en los secretos.")
            else:
                try:
                    with st.spinner("📖 Extrayendo conceptos clave..."):
                        result = generate_glossary(st.session_state["pdf_text"])
                        if result:
                            st.session_state["glossary"] = result
                            save_session_to_db()
                            st.rerun()
                except Exception as e:
                    st.error(f"Error interno capturado: {e}")

    with col3:
        if st.button("🎓 Crear Guía de Estudio", type="secondary", use_container_width=True):
            if not api_ready:
                st.error("⚠️ La API de Gemini no está configurada correctamente en los secretos.")
            else:
                try:
                    with st.spinner("🎓 Creando preguntas y test de estudio..."):
                        result = generate_study_guide(st.session_state["pdf_text"])
                        if result:
                            st.session_state["study_guide"] = result
                            save_session_to_db()
                            st.rerun()
                except Exception as e:
                    st.error(f"Error interno capturado: {e}")

    with col4:
        if st.button("🎙️ Generar Guion de Podcast", type="secondary", use_container_width=True):
            if not api_ready:
                st.error("⚠️ La API de Gemini no está configurada correctamente en los secretos.")
            else:
                try:
                    with st.spinner("🎙️ Escribiendo el guion del podcast (esto puede tardar un poco)..."):
                        texto_reducido = st.session_state["pdf_text"][:15000]
                        result = generar_podcast_api(texto_reducido)
                        if result:
                            st.session_state["guion_generado"] = result
                            save_session_to_db()
                            st.rerun()
                except Exception as e:
                    st.error(f"Error interno capturado: {e}")

    # Mostrar contenidos generados previamente o recién creados
    if st.session_state.get("resumen_generado"):
        st.markdown("### 📝 Resumen del Documento")
        st.markdown(st.session_state["resumen_generado"])
        st.download_button(
            label="📥 Descargar Resumen (.txt)",
            data=st.session_state["resumen_generado"],
            file_name="resumen_MeleLM.txt",
            mime="text/plain"
        )
        st.divider()

    if st.session_state.get("glossary"):
        st.markdown("### 📖 Glosario de Conceptos Clave")
        st.markdown(st.session_state["glossary"])
        st.divider()

    if st.session_state.get("study_guide"):
        st.markdown("### 🎓 Guía de Estudio")
        st.markdown(st.session_state["study_guide"])
        st.divider()

    if st.session_state.get("guion_generado"):
        with st.expander("🎙️ Guion del Podcast (Alex y Laura)", expanded=True):
            st.markdown(st.session_state["guion_generado"])
            st.download_button(
                label="📥 Descargar Guion de Podcast (.txt)",
                data=st.session_state["guion_generado"],
                file_name="guion_MeleLM.txt",
                mime="text/plain"
            )
        st.divider()

    # ==========================================
    # Sección de Chat Interactivo (Investigador Riguroso)
    # ==========================================
    st.subheader("💬 Chat interactivo con el documento")

    # Renderizar historial de conversación existente
    for message in st.session_state.get("chat_history", []):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input del usuario para nuevas preguntas
    if prompt := st.chat_input("Haz una pregunta sobre el contenido del documento..."):
        if not api_ready:
            st.error("⚠️ La API de Gemini no está configurada correctamente en los secretos.")
        else:
            try:
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                st.session_state["chat_history"].append({"role": "user", "content": prompt})

                with st.chat_message("assistant"):
                    with st.spinner("Analizando documento con rigor investigador..."):
                        response_text = answer_chat_question(
                            text=st.session_state["pdf_text"],
                            chat_history=st.session_state["chat_history"],
                            question=prompt
                        )
                        if response_text:
                            st.markdown(response_text)
                            st.session_state["chat_history"].append({"role": "assistant", "content": response_text})
                            save_session_to_db()
            except Exception as e:
                st.error(f"Error interno capturado: {e}")

elif not uploaded_files:
    st.info("Por favor, sube un archivo (PDF, DOCX o TXT) o selecciona una sesión anterior en la barra lateral para comenzar.")
