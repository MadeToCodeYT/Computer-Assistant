import cv2
import mediapipe as mp

mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)

    if result.multi_hand_landmarks:
        hand_landmarks = result.multi_hand_landmarks[-1]  # Only process the first detected hand
        finger_states = []

        # Landmark indices for finger tips and their lower points
        finger_tips = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky
        finger_pips = [3, 6, 10, 14, 18]  # Just below tips

        # Find hand type (left/right); default to right if not present
        hand_type = "Right"
        if hasattr(result, "multi_handedness"):
            try:
                hand_type = result.multi_handedness[-1].classification[0].label
            except Exception:
                pass

        # Convert landmarks into pixels instead of image size
        h, w, _ = frame.shape
        landmarks_px = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks.landmark]

        # Fix: Compute thumb state based on handedness
        # For right hand: thumb tip x > thumb pip x = open, else closed
        # For left hand: thumb tip x < thumb pip x = open, else closed
        if hand_type == "Right":
            thumb_state = "Open" if landmarks_px[4][0] < landmarks_px[3][0] else "Closed"
        else:
            thumb_state = "Open" if landmarks_px[4][0] > landmarks_px[3][0] else "Closed"
        finger_states.append(("Thumb", thumb_state))

        # Other fingers: tip.y < pip.y = open
        for i, name in zip([1, 2, 3, 4], ["Index", "Middle", "Ring", "Pinky"]):
            state = "Open" if landmarks_px[finger_tips[i]][1] < landmarks_px[finger_pips[i]][1] else "Closed"
            finger_states.append((name, state))

        print("Finger states:")
        for finger, state in finger_states:
            print(f"  {finger}: {state}")


    frame = cv2.flip(frame, 1)
    cv2.imshow("Hand Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
cap.release()
cv2.destroyAllWindows()