import streamlit as st
import io
import openai
import os
from dotenv import load_dotenv

# ======================
# CONFIGURAÇÃO INICIAL
# ======================
st.set_page_config(page_title="Professor de Inglês AI", layout="centered", initial_sidebar_state="collapsed")
load_dotenv()

# --- Carregamento das chaves ---
api_key = os.getenv("OPENROUTER_API_KEY") or st.secrets.get("OPENROUTER_API_KEY")

if not api_key:
    st.error("⚠️ Chave OPENROUTER_API_KEY não configurada.", icon="🚨")
    st.stop()

# --- Inicialização do Cliente ---
client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
    default_headers={"HTTP-Referer": "https://quizia.app", "X-Title": "Quizia App"},
)

# --- MODELOS DE IA ---
# Usamos o Llama 3 70B por ser excelente em seguir instruções complexas (como a correção)
# --- MODELOS DE IA ---

#MODELO_CHATBOT = "meta-llama/llama-3-70b-instruct:free" 

MODELO_CHATBOT = "google/gemma-3-27b-it:free" 
MODELO_TTS = "openai/tts-1"
MODELO_STT = "openai/whisper-1"

# ==================================================
# PROMPT DO SISTEMA (A "PERSONALIDADE" DA IA)
# ==================================================
SYSTEM_PROMPT = """
You are "Ivy", a friendly, patient, and professional AI English teacher (ESL).
Your goal is to help the user practice their conversational English.
Your responses MUST be entirely in English, as this is an immersive lesson.

Follow this structure for EVERY response:

1.  **Corrections:**
    * Analyze the user's last message for grammar, vocabulary, or pronunciation errors.
    * If there are mistakes, create a list. For each mistake:
        * `User said:` "[The user's incorrect phrase]"
        * `Better way:` "[The corrected phrase]"
        * `Explanation:` (A simple, brief explanation of the grammar rule or why it's better).
    * If there are NO mistakes, simply say: "Your English in that last message was perfect! Great job."

2.  **Your Response:**
    * After the corrections block, provide your own conversational reply.
    * Your reply should be natural, friendly, and directly address what the user said.
    * End your response with a follow-up question to keep the conversation flowing.

Do not be repetitive. Be encouraging and make the user feel comfortable practicing.
"""

# ==================================================
# FUNÇÕES DO ASSISTENTE DE VOZ
# ==================================================

def transcribe_audio_to_text(audio_bytes):
    """
    Converte a voz do usuário em texto (STT).
    """
    if not client or not audio_bytes:
        return None
    try:
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "recording.wav"
        
        transcription = client.audio.transcriptions.create(
            model=MODELO_STT,
            file=audio_file,
            language="en" # Força o reconhecimento em Inglês
        )
        return transcription.text
    except Exception as e:
        st.error(f"Erro ao transcrever áudio: {e}")
        return None

def get_teacher_response(history):
    """
    Gera a resposta da professora de inglês (LLM).
    """
    try:
        # Prepara as mensagens, incluindo o prompt do sistema
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(history) # Adiciona o histórico da conversa

        completion = client.chat.completions.create(
            model=MODELO_CHATBOT,
            messages=messages,
            timeout=180
        )
        return completion.choices[0].message.content
        
    except Exception as e:
        return f"Ocorreu um erro ao gerar a resposta: {e}"

def generate_audio_from_text(text_to_speak, voice="nova"):
    """
    Converte o texto da IA em voz (TSS).
    (Usando a voz 'nova' que tem um sotaque americano claro)
    """
    if not client or not text_to_speak:
        return None
    try:
        response = client.audio.speech.create(
            model=MODELO_TTS,
            voice=voice,
            input=text_to_speak
        )
        return response.content
    except Exception as e:
        st.error(f"Erro ao gerar áudio TTS: {e}")
        return None

# ======================
# INICIALIZAÇÃO DO ESTADO
# ======================
if "chat_messages" not in st.session_state:
    # Começa a conversa com a mensagem de boas-vindas da IA
    welcome_message = "Hi there! I'm Ivy, your personal English tutor. Let's start our conversation. How are you doing today?"
    
    # Gera o áudio da mensagem de boas-vindas
    with st.spinner("Loading your teacher, Ivy..."):
        audio_bytes = generate_audio_from_text(welcome_message)
    
    st.session_state.chat_messages = [{
        "role": "assistant",
        "content": welcome_message,
        "audio": audio_bytes # Salva o áudio
    }]

# ====================================================================
# INTERFACE STREAMLIT
# ====================================================================

st.title("🤖 Ivy: Sua Professora de Inglês por IA")
st.markdown("Pratique sua conversação. Pressione o microfone para falar em inglês, e a Ivy irá responder e corrigir seus erros.")

# --- Lógica Central de Chat ---
def process_chat_message(prompt_text):
    """Recebe um texto (de voz ou teclado) e completa o ciclo de chat."""
    
    # 1. Adiciona a mensagem do usuário
    st.session_state.chat_messages.append({"role": "user", "content": prompt_text})
    with st.chat_message("user"):
        st.markdown(prompt_text)

    # 2. Gera e exibe a resposta da IA (Professora)
    with st.chat_message("assistant"):
        with st.spinner("Ivy is thinking..."):
            response_text = get_teacher_response(st.session_state.chat_messages)
            st.markdown(response_text)
        
        # 3. Gera e toca o áudio (TTS)
        with st.spinner("Generating audio..."):
            audio_bytes_tts = generate_audio_from_text(response_text)
            if audio_bytes_tts:
                st.audio(audio_bytes_tts, format="audio/mp3", autoplay=True)
                st.session_state.chat_messages.append({
                    "role": "assistant", 
                    "content": response_text,
                    "audio": audio_bytes_tts 
                })
            else:
                st.session_state.chat_messages.append({
                    "role": "assistant", 
                    "content": response_text
                })

# --- Fim da Lógica Central de Chat ---

# Exibe o histórico do chat
for message in st.session_state.chat_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "audio" in message:
            st.audio(message["audio"], format="audio/mp3")

# --- Entradas de Voz (STT) e Texto ---
st.markdown("---")
col1, col2 = st.columns([6, 1])
with col1:
    # Entrada de texto (como fallback)
    prompt_text_input = st.chat_input("...ou digite em inglês")
with col2:
    # Entrada de voz
    st.markdown("""
    <style>
    div[data-testid="stAudioRecorder"] > button {
        width: 50px; height: 50px; border-radius: 50%;
        border: none; background-color: #FF4B4B; color: white;
    }
    div[data-testid="stAudioRecorder"] > button > svg { width: 60%; height: 60%; }
    </style>
    """, unsafe_allow_html=True)
    audio_bytes = st.audio_input("Grave sua voz")

    if audio_bytes is not None:
        st.audio(audio_bytes)
        with open("audio_user.wav", "wb") as f:
            f.write(audio_bytes.getbuffer())

# Processa a entrada de voz
if audio_bytes:
    with st.spinner("Transcribing your voice..."):
        prompt_from_audio = transcribe_audio_to_text(audio_bytes)
    if prompt_from_audio:
        process_chat_message(prompt_from_audio)

# Processa a entrada de texto
elif prompt_text_input:
    process_chat_message(prompt_text_input)
