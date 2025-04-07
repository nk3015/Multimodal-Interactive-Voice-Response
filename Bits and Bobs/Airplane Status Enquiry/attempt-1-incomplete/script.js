// Initialize Speech Synthesis and Speech Recognition
const synth = window.speechSynthesis;
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = new SpeechRecognition();

recognition.interimResults = false;
recognition.continuous = false;
recognition.lang = 'en-US';

let dialogueInProgress = false; // Track if a dialogue is still speaking
let ivrScript = {}; // Placeholder for IVR script data

// Fetch IVR Script from JSON File
fetch("screens.json")
    .then(response => response.json())
    .then(data => {
        ivrScript = data;
    });

function speakTextWithDisplay(text) {
    const utterance = new SpeechSynthesisUtterance(text);
    dialogueInProgress = true;

    // Display text on screen
    document.getElementById("ivr-display").innerText = text;

    synth.speak(utterance);

    utterance.onend = () => {
        dialogueInProgress = false;
    };
}

// IVR Flow
function startIVR() {
    speakTextWithDisplay(ivrScript.welcome);
    listenForInput();
}

function listenForInput() {
    recognition.start();

    recognition.onresult = (event) => {
        const userInput = event.results[0][0].transcript.toLowerCase();
        handleIVRInput(userInput);
    };

    recognition.onerror = () => {
        speakTextWithDisplay("Sorry.");
        listenForInput(); // Repeat dialogue on error
    };
}

function handleIVRInput(input) {
    if (dialogueInProgress) {
        synth.cancel(); // Stop the current dialogue if user responds early
        dialogueInProgress = false;
    }

    if (input.includes("check status")) {
        speakTextWithDisplay(ivrScript.checkStatus);
        recognition.start();
        recognition.onresult = (event) => {
            const flightNumber = event.results[0][0].transcript;
            speakTextWithDisplay(`You said flight number ${flightNumber}. Checking status now...`);
            // Add functionality to fetch flight status.
        };
    } else if (input.includes("flight schedule")) {
        speakTextWithDisplay(ivrScript.flightSchedule);
        recognition.start();
        recognition.onresult = (event) => {
            const destination = event.results[0][0].transcript;
            speakTextWithDisplay(`You said destination ${destination}. Fetching schedule now...`);
            // Add functionality to fetch flight schedule.
        };
    } else if (input.includes("exit")) {
        speakTextWithDisplay(ivrScript.exit);
    } else {
        speakTextWithDisplay(ivrScript.invalidOption);
        listenForInput();
    }
}