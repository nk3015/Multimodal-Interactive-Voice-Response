// Initialize Speech Synthesis and Speech Recognition
const synth = window.speechSynthesis;
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = new SpeechRecognition();

recognition.interimResults = false;
recognition.continuous = false;
recognition.lang = 'en-US';

let dialogueInProgress = false; // Track if a dialogue is speaking
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

// Start the IVR flow
function startIVR() {
    toggleButtons("call");
    speakTextWithDisplay(ivrScript.welcome);
    generateButtons(ivrScript.options);
    listenForInput();
}

// End the IVR call
function endCall() {
    toggleButtons("endCall");
    speakTextWithDisplay("Call ended. Thank you for using Airplane Status Inquiry.");
    clearButtons();
}

function listenForInput() {
    recognition.start();

    recognition.onresult = (event) => {
        const userInput = event.results[0][0].transcript.toLowerCase();
        console.log(userInput)
        // Show recognized input dynamically
        document.getElementById("ivr-display").innerText = `You said: "${userInput}"`;
        handleIVRInput(userInput);
    };

    recognition.onerror = () => {
        speakTextWithDisplay("Sorry.");
        listenForInput(); // Repeat dialogue on error
    };
}

function handleIVRInput(input) {
    if (dialogueInProgress) {
        synth.cancel(); // Interrupt ongoing dialogue if user responds early
        dialogueInProgress = false;
    }

    let matchedOption = ivrScript.options.find(option => input.includes(option.label.toLowerCase()));

    if (matchedOption) {
        speakTextWithDisplay(ivrScript[matchedOption.action]);
        // Perform specific action based on the input
        if (matchedOption.action === "exit") endCall();
    } else {
        speakTextWithDisplay(ivrScript.invalidOption);
        listenForInput();
    }
}

// Generate buttons dynamically based on JSON configuration
function generateButtons(options) {
    const buttonsContainer = document.getElementById("ivr-buttons");
    buttonsContainer.innerHTML = ""; // Clear existing buttons

    options.forEach(option => {
        const button = document.createElement("button");
        button.innerText = option.label;
        button.onclick = () => handleIVRInput(option.label.toLowerCase());
        buttonsContainer.appendChild(button);
    });
}

// Clear dynamically generated buttons
function clearButtons() {
    const buttonsContainer = document.getElementById("ivr-buttons");
    buttonsContainer.innerHTML = "";
}

// Toggle buttons between Call and End Call
function toggleButtons(state) {
    const callButton = document.getElementById("call-button");
    const endCallButton = document.getElementById("end-call-button");

    if (state === "call") {
        callButton.classList.add("hidden");
        endCallButton.classList.remove("hidden");
        document.getElementById("ivr-display").innerText = "Call in progress...";
    } else if (state === "endCall") {
        callButton.classList.remove("hidden");
        endCallButton.classList.add("hidden");
        document.getElementById("ivr-display").innerText = "Press 'Call' to start the inquiry.";
    }
}