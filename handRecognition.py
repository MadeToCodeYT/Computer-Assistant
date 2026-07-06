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
        hand_landmarks = result.multi_hand_landmarks[0]  # Only process the first detected hand
        finger_states = []

        # Landmark indices for finger tips and their lower points
        finger_tips = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky
        finger_pips = [3, 6, 10, 14, 18]  # Just below tips

        # Convert landmarks into pixels instead of image size
        h, w, _ = frame.shape
        landmarks_px = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks.landmark]

        # Assuming user is using right hand and palm is facing the camera
        thumb_state = "Closed" if landmarks_px[4][0] < landmarks_px[3][0] else "Open"
        finger_states.append(("Thumb", thumb_state))

        # Other fingers: tip.y < pip.y = open
        for i, name in zip([1, 2, 3, 4], ["Index", "Middle", "Ring", "Pinky"]):
            state = "Open" if landmarks_px[finger_tips[i]][1] < landmarks_px[finger_pips[i]][1] else "Closed"
            finger_states.append((name, state))

        print("Finger states:")
        for finger, state in finger_states:
            print(f"  {finger}: {state}")

        mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)


    frame = cv2.flip(frame, 1)
    cv2.imshow("Hand Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
cap.release()
cv2.destroyAllWindows()