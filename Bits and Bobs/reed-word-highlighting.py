import streamlit as st
import speech_recognition as sr
import time

def highlight_text(full_text, spoken_words):
    words = full_text.split()
    highlighted_text = " "
    for word in words:
        if word.lower() in spoken_words:
            highlighted_text += f'<span style="background-color: yellow">{word}</span> '
        else:
            highlighted_text += f'{word} '
    return highlighted_text

def main():
    st.title("Live Speech Highlighting")
    full_text = st.text_area("Enter text to read:", "This is a test text to highlight while reading.")
    start_button = st.button("Start Listening")
    
    if start_button:
        st.session_state['spoken_words'] = set()
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        with mic as source:
            recognizer.adjust_for_ambient_noise(source)
            st.write("Listening...")
            while True:
                try:
                    audio = recognizer.listen(source, timeout=5)
                    spoken_text = recognizer.recognize_google(audio)
                    spoken_words = set(spoken_text.lower().split())
                    st.session_state['spoken_words'].update(spoken_words)
                    
                    highlighted = highlight_text(full_text, st.session_state['spoken_words'])
                    st.markdown(highlighted, unsafe_allow_html=True)
                except sr.UnknownValueError:
                    continue
                except sr.RequestError:
                    st.error("Error with speech recognition service.")
                    break
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    break
                time.sleep(0.5)

if __name__ == "__main__":
    main()
