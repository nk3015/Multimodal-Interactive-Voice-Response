import cv2
import mediapipe as mp
import numpy as np

# Initialize MediaPipe Face Mesh and Hands
mp_face_mesh = mp.solutions.face_mesh
mp_hands = mp.solutions.hands
face_mesh = mp_face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Define indices for eye landmarks
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

# Menu options
menu_options = ["Option 1", "Option 2", "Option 3", "Option 4"]
selected_option = 0  # Index of the currently selected option

# Hand gesture detection
def detect_pinch(hand_landmarks):
    # Get the landmarks for the thumb tip (4) and index finger tip (8)
    thumb_tip = hand_landmarks.landmark[4]
    index_tip = hand_landmarks.landmark[8]

    # Calculate the distance between the thumb tip and index finger tip
    distance = np.linalg.norm(np.array([thumb_tip.x, thumb_tip.y]) - np.array([index_tip.x, index_tip.y]))
    return distance < 0.05  # Threshold for pinch gesture

def detect_eye_closure(eye_landmarks):
    # Extract x, y coordinates of upper and lower eyelids
    upper_lid = np.array([eye_landmarks[1].x, eye_landmarks[1].y])
    lower_lid = np.array([eye_landmarks[4].x, eye_landmarks[4].y])

    # Calculate the vertical distance between upper and lower eyelids
    distance = np.linalg.norm(upper_lid - lower_lid)
    return distance < 0.02  # Threshold for eye closure (adjust as needed)

def detect_gaze(eye_landmarks):
    # Extract x, y coordinates of iris and eye center
    iris = np.array([eye_landmarks[0].x, eye_landmarks[0].y])
    eye_center = np.mean([[lm.x, lm.y] for lm in eye_landmarks], axis=0)

    # Calculate the vertical position of the iris relative to the eye center
    gaze_direction = iris[1] - eye_center[1]
    if gaze_direction < -0.02:  # Threshold for looking up
        return "up"
    elif gaze_direction > 0.02:  # Threshold for looking down
        return "down"
    else:
        return "center"

def draw_menu(frame, selected_option):
    # Draw the menu options on the frame
    frame_height, frame_width, _ = frame.shape
    option_height = frame_height // (len(menu_options) + 1)  # Equal spacing for options

    for i, option in enumerate(menu_options):
        y = (i + 1) * option_height
        color = (0, 255, 0) if i == selected_option else (255, 255, 255)  # Highlight selected option
        cv2.putText(frame, option, (50, y), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

def draw_gaze_marker(frame, gaze_direction):
    # Draw a marker indicating the gaze direction
    frame_height, frame_width, _ = frame.shape
    if gaze_direction == "up":
        cv2.putText(frame, "Looking UP", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    elif gaze_direction == "down":
        cv2.putText(frame, "Looking DOWN", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

def draw_eye_landmarks(frame, eye_landmarks):
    # Draw the eye landmarks on the frame
    for landmark in eye_landmarks:
        x = int(landmark.x * frame.shape[1])
        y = int(landmark.y * frame.shape[0])
        cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)

def draw_hand_landmarks(frame, hand_landmarks):
    # Draw the hand landmarks on the frame
    for landmark in hand_landmarks.landmark:
        x = int(landmark.x * frame.shape[1])
        y = int(landmark.y * frame.shape[0])
        cv2.circle(frame, (x, y), 2, (255, 0, 0), -1)

def main():
    global selected_option
    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Convert the frame to RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results_face = face_mesh.process(image)
        results_hands = hands.process(image)

        # Reset gaze direction
        gaze_direction = "center"

        if results_face.multi_face_landmarks:
            for face_landmarks in results_face.multi_face_landmarks:
                # Extract eye landmarks
                left_eye = [face_landmarks.landmark[i] for i in LEFT_EYE]
                right_eye = [face_landmarks.landmark[i] for i in RIGHT_EYE]

                # Draw eye landmarks
                draw_eye_landmarks(frame, left_eye)
                draw_eye_landmarks(frame, right_eye)

                # Detect eye closure
                if detect_eye_closure(left_eye) and detect_eye_closure(right_eye):
                    print("Eyes firmly shut")
                    # Trigger action for eye closure (e.g., select the current option)
                    print(f"Selected: {menu_options[selected_option]}")

                # Detect gaze direction
                gaze_direction = detect_gaze(left_eye)
                print(f"Gaze direction: {gaze_direction}")

                # Update selected option based on gaze direction
                if gaze_direction == "up":
                    selected_option = max(0, selected_option - 1)  # Move selection up
                elif gaze_direction == "down":
                    selected_option = min(len(menu_options) - 1, selected_option + 1)  # Move selection down

        # Hand tracking for pinch gesture
        if results_hands.multi_hand_landmarks:
            for hand_landmarks in results_hands.multi_hand_landmarks:
                # Draw hand landmarks
                draw_hand_landmarks(frame, hand_landmarks)

                # Detect pinch gesture
                if detect_pinch(hand_landmarks):
                    print("Pinch detected! Clicking...")
                    print(f"Selected: {menu_options[selected_option]}")

        # Draw the menu and gaze marker
        draw_menu(frame, selected_option)
        draw_gaze_marker(frame, gaze_direction)

        # Display the frame
        cv2.imshow('Eye Gaze + Hand Tracking', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()