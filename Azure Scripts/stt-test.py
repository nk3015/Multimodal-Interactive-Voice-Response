import azure.cognitiveservices.speech as speechsdk

speech_key = "2JNju08Ih1lBPu3XDTSgmID407Qiavc3nswqYXPeaTlhs3UVWw7jJQQJ99BBAClhwhEXJ3w3AAAYACOG592K"  
service_region = "ukwest"  

def from_mic():
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

    print("Speak into your microphone.")
    speech_recognition_result = speech_recognizer.recognize_once_async().get()
    print(speech_recognition_result.text)

from_mic()