import azure.cognitiveservices.speech as speechsdk  

# Generate your own key and region through the Speech Service on Azure
speech_key = "2JNju08Ih1lBPu3XDTSgmID407Qiavc3nswqYXPeaTlhs3UVWw7jJQQJ99BBAClhwhEXJ3w3AAAYACOG592K"  
service_region = "ukwest"  

speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)  
speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"
audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)  

synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)  

''' ssml = """
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
    <voice name="en-US-JennyNeural">
        <prosody rate="0%" pitch="+5%"> <!-- This line is the issue -->
            <mstts:express-as style="cheerful">
                Hello, caller! I am the voice for your IVR system.
            </mstts:express-as>
    </voice>
</speak>
""" '''

ssml = """
<speak version=\'1.0\' xmlns=\'http://www.w3.org/2001/10/synthesis\' xml:lang=\'en-US\'>
    <voice name=\'en-US-AriaNeural\'> Hello world!</voice>
</speak> """

#synthesizer.speak_text_async("Hello, caller! I am the voice for yourS IVR system.").get()  

synthesizer.speak_ssml_async(ssml).get()