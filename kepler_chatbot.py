import streamlit as st
import pandas as pd
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
import tempfile
from pydub import AudioSegment
import os
import streamlit.components.v1 as components
from urllib.parse import urlparse, parse_qs

# --- CONFIGURE GOOGLE GEMINI ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("models/gemini-1.5-flash-latest")

# --- LOAD DATA FROM XLSX ---
try:
    df = pd.read_excel('Chatbot Questions & Answers.xlsx')
    qa_pairs = [f"Q: {q}\nA: {a}" for q, a in zip(df['Question'], df['Answer'])]
    context = "\n".join(qa_pairs)
except FileNotFoundError:
    st.error("Data file 'Chatbot Questions & Answers.xlsx' not found. Please make sure it's in the same directory.")
    st.stop()

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kepler CampusBot", layout="wide")

# --- Sidebar Navigation ---
with st.sidebar:
    # Use a native Streamlit image component for the logo
    st.image("kepler-logo.png", width=120)
    st.header("Navigation")

    if st.button("🏠 Home", use_container_width=True, key="home_btn"):
        st.query_params['page'] = 'home'
        st.rerun()
    if st.button("💬 Chatbot", use_container_width=True, key="chat_btn"):
        st.query_params['page'] = 'chat'
        st.rerun()
    if st.button("ℹ️ About Me", use_container_width=True, key="about_btn"):
        st.query_params['page'] = 'about'
        st.rerun()

# --- MAIN CONTENT AREA: DISPLAY PAGE BASED ON URL PARAMETER ---
current_page = st.query_params.get('page', 'home')

if current_page == "home":
    # --- Home Page Content (Embedded HTML) ---
    st.markdown("<style>body {overflow-x: hidden;}</style>", unsafe_allow_html=True) # Hide scrollbar
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        components.html(html_content, height=800, scrolling=True) # Embed the HTML
    except FileNotFoundError:
        st.error("Error: 'index.html' not found. Please make sure it's in the same directory.")

    # --- ADDED: Call to Action and Styled Button ---
    st.markdown("<br><br><br>", unsafe_allow_html=True) # Add some spacing
    
    # This section is designed to be horizontally centered on the page
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Add the requested text, centered and styled
        st.markdown("<h2 style='text-align: center; font-weight: bold; color: #2A527A;'>Ready to explore more about Kepler?</h2>", unsafe_allow_html=True)
        st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True) # Add spacing below the text
        
        # Button styling CSS
        button_style = """
            <style>
            .stButton>button {
                background-color: #439947; /* Dominant green from your HTML */
                color: white;
                padding: 12px 30px;
                border: none;
                border-radius: 9999px; /* Fully rounded */
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                display: block; /* Makes the button a block element for centering */
                margin-left: auto;
                margin-right: auto;
            }
            .stButton>button:hover {
                background-color: #367a3a;
                transform: translateY(-2px);
                box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
            }
            </style>
        """
        st.markdown(button_style, unsafe_allow_html=True)
        
        # The button itself
        if st.button("🚀 Start Chatting Now", key="styled_native_start_btn"):
            st.query_params['page'] = 'chat'
            st.rerun()

    # --- Fixed footer as a Streamlit component ---
    footer_html = """
    <style>
    .fixed-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #2A527A; /* Tailwind's bg-gray-800 */
        color: white;
        text-align: center;
        padding: 1.5rem;
        font-size: 0.875rem; /* Tailwind's text-sm */
        z-index: 1000; /* Ensures it stays on top */
        box-shadow: 0 -4px 6px -1px rgba(0, 0, 0, 0.1), 0 -2px 4px -2px rgba(0, 0, 0, 0.06);
    }
    </style>
    <div class="fixed-footer">
        <p>© 2025 Kepler College. All rights reserved.</p>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)


elif current_page == "chat":
    # --- Chatbot Page Content ---
    st.image("kepler-logo.png", width=120)
    st.markdown("<h2 style='color:#2A527A; text-align:center;'>Welcome to Kepler CampusBot 🎓</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Ask about Kepler College rules, policies, or services. You can type or speak.</p>", unsafe_allow_html=True)

    # --- CHAT DISPLAY ---
    if "history" not in st.session_state:
        st.session_state.history = []

    for msg in st.session_state.history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # --- SPEECH TO TEXT FUNCTION ---
    # NOTE: This function uses hardcoded paths which are specific to your system.
    # You will need to change them if you move this code to a different computer.
    def transcribe_audio(audio_bytes_data):
        tmpfile_path = None
        try:
            # IMPORTANT: Update these paths if FFmpeg is installed in a different location.
            AudioSegment.converter = "C:/Aims/kepler_chatbot/ffmpeg-2025-06-26-git-09cd38e9d5-essentials_build/bin/ffmpeg.exe"
            AudioSegment.ffprobe = "C:/Aims/kepler_chatbot/ffmpeg-2025-06-26-git-09cd38e9d5-essentials_build/bin/ffprobe.exe"
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
                tmpfile.write(audio_bytes_data)
                tmpfile_path = tmpfile.name
            
            sound = AudioSegment.from_file(tmpfile_path)
            sound.export(tmpfile_path, format="wav")
            
            recognizer = sr.Recognizer()
            with sr.AudioFile(tmpfile_path) as source:
                audio = recognizer.record(source)
            
            return recognizer.recognize_google(audio)
        except FileNotFoundError:
            st.error("Error: FFmpeg or ffprobe not found. Please check your installation and paths.")
            return None
        except Exception as e:
            st.error(f"Error during audio transcription: {e}")
            return None
        finally:
            if tmpfile_path and os.path.exists(tmpfile_path):
                os.remove(tmpfile_path)

    # --- CHAT INPUT AREA WITH MICROPHONE (SIDE-BY-SIDE) ---
    col1, col2 = st.columns([1, 8])
    user_input = None
    with col1:
        audio_dict = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key='recorder', just_once=True)
        if audio_dict and 'bytes' in audio_dict:
            transcribed_text = transcribe_audio(audio_dict['bytes'])
            if transcribed_text:
                user_input = transcribed_text
    with col2:
        # Use a more explicit check to avoid triggering a new input if microphone is used
        typed_input = st.chat_input("Type your question...", key='chat_input_text')
        if typed_input:
            user_input = typed_input

    # --- PROCESS USER QUESTION ---
    if user_input:
        st.session_state.history.append({"role": "user", "content": user_input})
        with st.chat_message("user"): st.markdown(user_input)
        
        # --- Generate response from Gemini based on context ---
        prompt = f"""You are Kepler CampusBot. Use this Q&A to help answer:\n{context}\n\nUser: {user_input}"""
        response = model.generate_content(prompt)
        answer = response.text.strip()
        
        # --- Display and save assistant's response ---
        st.session_state.history.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"): st.markdown(answer)
        st.rerun()

    # --- ADDED: Auto-scroll to the bottom of the page on rerun ---
    # This JavaScript snippet runs on every page rerun and scrolls the view to the bottom.
    components.html(
        """
        <script>
            // This script runs on every page load/rerun and scrolls to the bottom.
            window.scrollTo(0, document.body.scrollHeight);
        </script>
        """,
        height=0,  # Make the component invisible
    )

elif current_page == "about":
    # --- About Me Page Content ---
    st.title("About Kepler CampusBot")
    st.markdown(
        """
        I am CampusBot, an AI assistant designed to help you with a wide range of tasks and questions about Kepler College. 
        My knowledge is based on official college resources, and my goal is to provide you with instant, accurate information.
        """
    )
    
    st.markdown("---") # Add a horizontal rule for separation

    st.markdown(
        """
        ### Contact Us
        For more detailed information, personalized assistance, or questions beyond my knowledge base, you can contact the Kepler College team:
        
        - **Phone:** `+250789773042`
        - **Website:** Visit the official Kepler website at [**keplercollege.ac.rw**](https://keplercollege.ac.rw)
        - **Admissions:** For admissions-related questions, contact the Admissions team at [**admissions@keplercollege.ac.rw**](mailto:admissions@keplercollege.ac.rw)
        """
    )
    
    st.markdown("---") # Add another horizontal rule

    st.markdown("""
        This application uses:
        - **Streamlit** for the user interface.
        - **Google Gemini 1.5 Flash** for natural language processing.
        - **`streamlit-mic-recorder`** for voice input.
        - **`SpeechRecognition`** and **`pydub`** to convert speech to text.
        """, unsafe_allow_html=True)
    if st.button("⬅️ Back to Home", type="primary"):
        st.query_params['page'] = 'home'
        st.rerun()