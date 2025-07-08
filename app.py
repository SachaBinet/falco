
import streamlit as st
import openai
import base64
import json
import re
import streamlit.components.v1 as components
import base64
from pathlib import Path
import streamlit as st
import ast

def extract_json_from_response(raw_text):
    try:
        start = raw_text.find('{')
        end = raw_text.rfind('}') + 1
        json_str = raw_text[start:end]
        return json.loads(json_str)
    except Exception as e:
        raise ValueError(f"Erreur lors du parsing JSON : {e}")

# Encode l’image du logo localement en base64
image_path = "assets/falco_logo.png"  # adapte ce chemin si besoin
with open(image_path, "rb") as img_file:
    image_b64 = base64.b64encode(img_file.read()).decode()


# --- Personnalisation CSS ---
def inject_custom_css():
    st.markdown("""
        <style>
        html, body {
            font-family: 'Segoe UI', 'Verdana', sans-serif;
            background-color: #ffffff;
        }
        .stTextArea textarea {
            font-size: 1.1rem;
            line-height: 1.6;
        }
        button {
            font-size: 1.1rem !important;
        }
        </style>
    """, unsafe_allow_html=True)

# --- Clé API depuis .streamlit/secrets.toml ---
openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- Prompt IA FALCO ---
FALCO_PROMPT = """
Tu es une IA spécialisée en accessibilité.

Je vais te fournir une image d’un document imprimé (menu, flyer, notice...).

Ta mission est d’en extraire les informations et de les rendre accessibles sous trois formes :

1. Gros caractères : mise en page simple, titres, phrases courtes
2. Version FALC (Facile à Lire et à Comprendre)
3. Version audio-friendly (phrases fluides, voix naturelle)

Je veux que tu dévrives ce que représente le document (menu de restaurant, notice, étiquette alimentaire, etc.).
S'il s'agit d'un menu de restaurant je veux la liste exhaustive de ce que tu y trouves.

Rends la réponse au format JSON, sans commentaire ni balise Markdown :
{
  "gros_texte": "...",
  "falc": "...",
  "audio": "..."
}

Ne réponds qu’avec un objet JSON. N'ajoute AUCUNE phrase ou explication.
"""

# --- Appel GPT-4o avec image ---
def call_gpt4o_with_image(image_bytes):
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": FALCO_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        temperature=0.3
    )
    raw = response.choices[0].message.content
    return extract_json_from_response(raw)

# --- Bouton vocal ---
def speak_js_block(text, label):
    escaped = text.replace("\\", "\\\\").replace("`", "\\`").replace("\n", "\\n").replace('"', '\\"')
    return f"""
    <script>
    function speak_{label}() {{
        var msg = new SpeechSynthesisUtterance();
        msg.text = `{escaped}`;
        msg.lang = 'fr-FR';
        window.speechSynthesis.speak(msg);
    }}
    </script>
    <button onclick="speak_{label}()">🔊 Lire le texte</button>
    """


def render_gros_texte_html(texte):
    texte_html = texte.replace('\n', '<br>')
    styled_html = f"""
    <div style="font-size: 2rem; line-height: 1.6; color: #000; background-color: #fff; padding: 1rem; border-radius: 0.5rem;">
        {texte_html}
    </div>
    """
    return styled_html

# --- Interface ---
st.set_page_config(page_title="FALCO - Accessibilité instantanée", page_icon="🦅")
inject_custom_css()

# Haut de page avec logo à gauche et texte à droite
st.markdown(f"""
<div style="display: flex; align-items: center; justify-content: flex-start; margin-top: 1rem; margin-bottom: 2.5rem;">
    <img src="data:image/png;base64,{image_b64}" alt="Logo FALCO" style="height: 120px; margin-right: 1.5rem;">
    <div style="font-size: 1.2rem; color: #222; line-height: 1.5;">
        <strong>Bienvenue chez FALCO</strong>, votre compagnon d’accessibilité.<br>
        Ici, une simple image devient un support lisible, compréhensible et écoutable.
    </div>
</div>
""", unsafe_allow_html=True)


# Choix Import
##st.markdown("### 📥 Importer un document")

# Initialiser l'état par défaut au démarrage
if "option" not in st.session_state:
    st.session_state.option = "📸 Prendre une photo"

# Afficher deux boutons côte à côte
col1, col2 = st.columns(2)

with col1:
    if st.button("📸 Prendre une photo", use_container_width=True):
        st.session_state.option = "📸 Prendre une photo"

with col2:
    if st.button("📁 Charger une image", use_container_width=True):
        st.session_state.option = "📁 Charger une image"

# Accès à l'option sélectionnée
option = st.session_state.option


image_bytes = None
if option == "📸 Prendre une photo":
    photo = st.camera_input("Prenez une photo du document")
    if photo:
        image_bytes = photo.getvalue()
elif option == "📁 Charger une image":
    uploaded_file = st.file_uploader("Importez un fichier image", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        image_bytes = uploaded_file.read()

if image_bytes:
    st.image(image_bytes, caption="Image sélectionnée", use_container_width=True)

    with st.spinner("🧠 FALCO analyse l’image..."):
        try:
            result = call_gpt4o_with_image(image_bytes)
        except Exception as e:
            st.error(f"Erreur lors du traitement : {e}")
            st.stop()

    st.success("✅ Analyse terminée ! Voici les versions accessibles générées :")

    with st.expander("👓 Version Gros caractères", expanded=True):
        st.markdown(render_gros_texte_html(result["gros_texte"]), unsafe_allow_html=True)

    with st.expander("📘 Version FALC", expanded=False):
        st.text_area("Texte FALC", value=result["falc"], height=200)
        components.html(speak_js_block(result["falc"], "falc"), height=60)

    with st.expander("🔉 Version audio-friendly", expanded=False):
        st.text_area("Texte vocal", value=result["audio"], height=200)
        components.html(speak_js_block(result["audio"], "audio"), height=60)
