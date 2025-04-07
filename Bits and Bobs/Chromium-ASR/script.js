// Check if browser supports SpeechRecognition
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (SpeechRecognition) {
    const recognition = new SpeechRecognition();
    recognition.continuous = true; //false; // Stop after one result
    recognition.interimResults = false; // Return only final result
    recognition.lang = "en-US"; // Set language

    recognition.onstart = () => {
        console.log("Speech recognition started...");
    };

    recognition.onspeechend = () => {
        console.log("Speech recognition ended.");
        recognition.stop();
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        console.log("Recognized speech:", transcript);
        document.getElementById("output").innerText = transcript;
    };

    recognition.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
    };

    document.getElementById("start").addEventListener("click", () => {
        recognition.start();
    });

} else {
    console.error("Web Speech API is not supported in this browser.");
}
