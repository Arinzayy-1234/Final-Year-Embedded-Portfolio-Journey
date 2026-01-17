
import mediapipe as mp
import cv2
import math
"""
About rawMp.py
This handles AI Logic
"""

class RawHandDetector:

    def __init__(self, mode=False, max_hands=2, detection_con=0.5, track_con=0.5):
        self.mode = mode
        self.max_hands = max_hands
        self.detection_con = detection_con
        self.track_con = track_con

        # Accessing the mediapipe Hand library
        self.hand_engine = mp.solutions.hands # Shortcut to hands.py
        self.hand_tracker = self.hand_engine.Hands ( # the instance of the tracker model
            static_image_mode=self.mode,
            max_num_hands=self.max_hands,
            min_detection_confidence=self.detection_con,
            min_tracking_confidence=self.track_con
        )
        self.draw_utils = mp.solutions.drawing_utils # Shortcut to drawing_utils.py
        self.tip_ids = [4,8,12,16,20] # Thumb,Index,Middle,Ring,Pinky


    def find_hands(self, frame, draw=True):

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        self.hand_data = self.hand_tracker.process(frame_rgb) # The instance of the Tracker AI model should process the frame

        if self.hand_data.multi_hand_landmarks:

            for hand_object in self.hand_data.multi_hand_landmarks:

                if draw:
                    self.draw_utils.draw_landmarks(frame, hand_object, self.hand_engine.HAND_CONNECTIONS)
                    
        return frame # if this was frame_rgb it will return rgb frame and when it is displayed it will give wierd cool colors 😂
        
    def find_position(self, frame, hand_indexes=[0], draw=True):
        
        landmark_list = []

        if self.hand_data.multi_hand_landmarks:
            for hand_index in hand_indexes:
                if hand_index < len(self.hand_data.multi_hand_landmarks):
                    hand_object = self.hand_data.multi_hand_landmarks[hand_index]
                    for id, landmark_object in enumerate(hand_object.landmark):
                        
                        h, w, c = frame.shape

                        x_pixels , y_pixels = int(landmark_object.x * w) , int (landmark_object.y * h)

                        landmark_list.append([id, x_pixels, y_pixels])
        
                        if draw:
                            cv2.circle(frame, (x_pixels, y_pixels), 5,  (255,0,255), cv2.FILLED)

        return landmark_list



            
    
