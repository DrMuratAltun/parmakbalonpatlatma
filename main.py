import cv2
import mediapipe as mp
import numpy as np
import time
import random

class Balloon:
    def __init__(self, width, height):
        self.radius = random.randint(30, 60)
        self.x = random.randint(self.radius, width - self.radius)
        self.y = height + self.radius
        self.speed = random.randint(3, 7)
        self.color = (random.randint(0,255), random.randint(0,255), random.randint(0,255))

    def move(self):
        self.y -= self.speed

    def draw(self, frame):
        cv2.circle(frame, (self.x, self.y), self.radius, self.color, -1)
        cv2.circle(frame, (self.x, self.y), self.radius, (0,0,0), 2)

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

cap = cv2.VideoCapture(0)
width, height = 800, 600
cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

# Oyun durum değişkenleri
game_active = True
balloons = []
score = 0
start_time = time.time()
game_duration = 60  # 60 saniye

# Yeniden başlat butonu özellikleri
button_pos = (width//2-100, height//2+100)
button_size = (200, 60)  # (genişlik, yükseklik)

def reset_game():
    global game_active, score, start_time, balloons
    game_active = True
    score = 0
    start_time = time.time()
    balloons = []

with mp_hands.Hands(
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
    max_num_hands=1) as hands:

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            continue

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        finger_tip = None
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                landmark = hand_landmarks.landmark[8]
                x = int(landmark.x * width)
                y = int(landmark.y * height)
                finger_tip = (x, y)
                cv2.circle(frame, (x,y), 10, (0,255,0), -1)

        if game_active:
            # Yeni balon ekleme
            if random.random() < 0.05:
                balloons.append(Balloon(width, height))

            # Balonları hareket ettir ve kontrol et
            remaining_balloons = []
            for balloon in balloons:
                balloon.move()
                balloon.draw(frame)
                
                if balloon.y + balloon.radius < 0:
                    continue
                    
                if finger_tip:
                    distance = np.hypot(balloon.x - finger_tip[0], balloon.y - finger_tip[1])
                    if distance < balloon.radius:
                        score += 1
                        continue
                        
                remaining_balloons.append(balloon)
                
            balloons = remaining_balloons

            # Zaman kontrolü
            elapsed_time = time.time() - start_time
            remaining_time = max(game_duration - int(elapsed_time), 0)
            
            if elapsed_time > game_duration:
                game_active = False

        # Oyun durumu göstergeleri
        cv2.putText(frame, f"Time: {remaining_time}s" if game_active else "Time: 0s", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
        cv2.putText(frame, f"Score: {score}", (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

        # Oyun bitiş ekranı
        if not game_active:
            # Oyun bitiş metni
            cv2.putText(frame, "OYUN BITTI!", (width//2-150, height//2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 4)
            cv2.putText(frame, f"Final Skor: {score}", (width//2-150, height//2+50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
            
            # Yeniden başlat butonu
            button_color = (200, 100, 50)
            # Buton vurgulama (parmak üzerindeyse)
            if finger_tip and (button_pos[0] < finger_tip[0] < button_pos[0]+button_size[0] and 
                             button_pos[1] < finger_tip[1] < button_pos[1]+button_size[1]):
                button_color = (200, 150, 100)
                # Tıklama algılama
                if any(ln.landmark[8].z < ln.landmark[7].z for ln in results.multi_hand_landmarks):
                    reset_game()
            
            # Buton çizimi
            cv2.rectangle(frame, 
                         button_pos, 
                         (button_pos[0]+button_size[0], button_pos[1]+button_size[1]), 
                         button_color, -1)
            cv2.putText(frame, "YENIDEN BASLAT", (button_pos[0]+10, button_pos[1]+40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)

        cv2.imshow('Balloon Pop Game', frame)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()