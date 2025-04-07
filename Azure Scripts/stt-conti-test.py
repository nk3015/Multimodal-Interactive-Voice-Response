import azure.cognitiveservices.speech as speechsdk

def recognize_speech_continuous():
    # Set up your Azure Speech configuration
    speech_key = "2JNju08Ih1lBPu3XDTSgmID407Qiavc3nswqYXPeaTlhs3UVWw7jJQQJ99BBAClhwhEXJ3w3AAAYACOG592K"  
    service_region = "ukwest" 
    
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    
    def recognizing_handler(evt):
        print(f"Recognizing: {evt.result.text}")
    
    def recognized_handler(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            print(f"Recognized: {evt.result.text}")
        elif evt.result.reason == speechsdk.ResultReason.NoMatch:
            print("No speech could be recognized.")
    
    def canceled_handler(evt):
        print(f"Canceled: {evt.reason}")
        if evt.reason == speechsdk.CancellationReason.Error:
            print(f"Error details: {evt.error_details}")
    
    speech_recognizer.recognizing.connect(recognizing_handler)
    speech_recognizer.recognized.connect(recognized_handler)
    speech_recognizer.canceled.connect(canceled_handler)
    
    print("Starting continuous recognition. Speak into the microphone.")
    speech_recognizer.start_continuous_recognition()
    
    try:
        while True:
            pass  # Keep the script running
    except KeyboardInterrupt:
        print("Stopping recognition...")
        speech_recognizer.stop_continuous_recognition()

if __name__ == "__main__":
    recognize_speech_continuous()
