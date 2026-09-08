# 🤖 Integración de Google Gemini en MeleLM

Documentación de arquitectura, configuración y modelos utilizados en la aplicación **MeleLM** para el análisis inteligente de documentos mediante la API de Google Gemini.

---

## 📌 Visión General

MeleLM utiliza el SDK oficial de **Google Generative AI (`google-generativeai`)** en Python para interactuar con los modelos de inteligencia artificial de Google. La aplicación realiza extracción de contexto a partir de archivos subidos por el usuario (`.pdf`, `.docx`, `.txt`) y genera diversos artefactos educativos y respuestas conversacionales en tiempo real.

---

## ⚡ Modelo Activo

Actualmente, el sistema utiliza la versión oficial del modelo gratuito de alta velocidad:

- **Modelo predeterminado**: `gemini-1.5-flash`
- **Razones de elección**:
  - Tasa de límites (Quota Rate Limits) óptima para cuentas gratuitas.
  - Ventana de contexto amplia (hasta 1 millon de tokens).
  - Respuestas ultra-rápidas compatibles con streaming en el chat.

---

## ⚙️ Configuración e Inicialización

La inicialización de la API de Gemini se realiza dinámicamente mediante los secretos de Streamlit (`.streamlit/secrets.toml`):

```python
import google.generativeai as genai
import streamlit as st

def init_gemini_api():
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        st.session_state["model"] = "gemini-1.5-flash"
        return True
    except KeyError:
        st.error("⚠️ No se ha encontrado la clave 'GEMINI_API_KEY' en los secretos de Streamlit.")
        return False
```

---

## 🛠️ Funcionalidades e Integraciones

### 1. 📝 Generación de Resúmenes
- **Función**: `generar_resumen_api(texto_reducido)`
- **Cache**: `@st.cache_data` para optimizar llamadas repetidas sobre el mismo contenido.
- **Formato**: Viñetas estructuradas con puntos clave y conclusiones.

### 2. 📖 Glosario de Conceptos Clave
- **Función**: `generate_glossary(text)`
- **Extracción**: Identifica y define los 10 términos más relevantes basados estrictamente en el texto del documento.

### 3. 🎓 Guía de Estudio y Test
- **Función**: `generate_study_guide(text)`
- **Estructura**:
  - 5 Preguntas de desarrollo con respuesta explicativa.
  - 5 Preguntas tipo test (opciones A, B, C, D) con soluciones al final.

### 4. 🎙️ Guion de Podcast
- **Función**: `generar_podcast_api(texto_reducido)`
- **Formato**: Diálogo ameno y divulgativo entre dos locutores (*Alex* y *Laura*).

### 5. 💬 Chat Conversacional en Streaming
- **Modelo**: `model.generate_content(prompt_text, stream=True)`
- **Control de Flujo**: La llamada a la API únicamente se ejecuta tras la entrada directa del usuario (`if prompt_actual:`), evitando consumos de cuota o llamadas automáticas al recargar la página.

---

## 📋 Requisitos de Dependencias

En `requirements.txt`:
```txt
google-generativeai>=0.5.2
```
Garantiza la compatibilidad con el modelo `gemini-1.5-flash` y las API estructuradas de Gemini 1.5.
