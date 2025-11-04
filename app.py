import streamlit as st
import io
import os
from dotenv import load_dotenv
from gtts import gTTS
from openai import OpenAI

# ======================
# CONFIGURAÇÃO INICIAL
# ======================
st.set_page_config(page_title="SpeakUp - Professor de Inglês AI", layout="centered", initial_sidebar_state="collapsed")
load_dotenv()

# ======================
# CHAVE DO OPENROUTER
# ======================
api_key_openrouter = os.getenv("OPENROUTER_API_KEY") or st.secrets.get("OPENROUTER_API_KEY")

if not api_key_openrouter:
    st.error("⚠️ A chave OPENROUTER_API_KEY não está configurada.", icon="🚨")
    st.stop()

# ======================
# CLIENTE OPENROUTER
# ======================
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key_openrouter,
)

# ======================
# INTERFACE PRINCIPAL
# ======================
st.title("🗣️ SpeakUp - Professor de Inglês AI")

st.markdown(
    """
    Pratique sua pronúncia, receba correções e escute as respostas com IA 💬🎧  
    Modelo usado: **Llama 3.3 70B Instruct (gratuito via OpenRouter)**  
    """
)

# ======================
# GRAVAÇÃO DE ÁUDIO
# ======================
st.markdown("### 🎤 Grave seu áudio")
audio_bytes = st.audio_input("Pressione para gravar sua voz")

if audio_bytes is not None:
    st.audio(audio_bytes)
    with open("audio_user.wav", "wb") as f:
        f.write(audio_bytes.getbuffer())
    st.success("✅ Áudio gravado com sucesso!")

# ======================
# CHAT E CORREÇÃO
# ======================
st.markdown("### 💬 Converse com o Professor de Inglês")

user_text = st.text_area("Digite ou grave algo em inglês:", placeholder="Ex: I go to the park yesterday...")

if st.button("Corrigir e responder"):
    if not user_text.strip():
        st.warning("Por favor, digite ou grave uma frase primeiro.")
    else:
        try:
            with st.spinner("✍️ O Professor está analisando sua frase..."):
                completion = client.chat.completions.create(
                    extra_headers={
                        "HTTP-Referer": "https://speakup.streamlit.app",
                        "X-Title": "SpeakUp App",
                    },
                    model="meta-llama/llama-3.3-70b-instruct:free",
                    messages=[
                        {
                            "role": "system",
                            "content": "Você é um professor de inglês paciente, que corrige e explica de forma simples e positiva."
                        },
                        {
                            "role": "user",
                            "content": user_text
                        }
                    ]
                )

                resposta = completion.choices[0].message.content

                st.markdown("### 🧠 Feedback do Professor")
                st.write(resposta)

                # ======================
                # GERAÇÃO DE ÁUDIO COM gTTS
                # ======================
                with st.spinner("🎧 Gerando áudio da resposta..."):
                    tts = gTTS(text=resposta, lang="en")
                    tts.save("tts_output.mp3")

                    with open("tts_output.mp3", "rb") as f:
                        audio_data = f.read()
                        st.audio(audio_data, format="audio/mp3")

        except Exception as e:
            st.error(f"Ocorreu um erro: {e}")

# ======================
# RODAPÉ
# ======================
st.markdown("---")
st.caption("Desenvolvido por Kennia Taisa • 🚀 Llama 3.3 70B + gTTS (gratuito)")
