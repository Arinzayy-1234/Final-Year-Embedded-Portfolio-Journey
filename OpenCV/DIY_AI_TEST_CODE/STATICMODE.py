import sys
import os
import numpy as np

# This tells Python to look one folder "up" for modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cv2
from rawMp import RawHandDetector
from python_virtual_hand import init_virtual_hand, send_to_virtual_hand

init_virtual_hand() # launches pygame window in the background

FINGER_POINTS = {
    "Thumb": {"tip": 4,  "base" : 1},
    "Index": {"tip": 8 , "base":  5 },
    "Middle":{"tip": 12, "base":  9},
    "Ring":  {"tip": 16, "base":  13},
    "Pinky": {"tip": 20, "base":  17},
}

# Permanent Storage for closed and open ratios

open_calibra = {}
close_calibra = {} 

cap = cv2.VideoCapture(0)

arinze_hand = RawHandDetector()

is_frozen = False

frame = None



def get_finger_curl_ratio(landmark_list, tip_idx, base_idx, wrist_idx=0):
    """
    Calculates the curl ratio for a finger based on the Tip-to-Wrist distance,
    normalized by the Palm Size (Wrist-to-Base Knuckle).
    """
    # 1. Extract coordinates from the landmark_list [id, x, y]
    # We use index 1 for x and index 2 for y
    tip   = np.array([landmark_list[tip_idx][1],   landmark_list[tip_idx][2]])
    base  = np.array([landmark_list[base_idx][1],  landmark_list[base_idx][2]])
    wrist = np.array([landmark_list[wrist_idx][1], landmark_list[wrist_idx][2]])

    # 2. Calculate the "Tendon" distance (Tip to Wrist). It gives pythagoras theorem vibes.
    tip_to_wrist = np.linalg.norm(tip - wrist)

    # 3. Calculate the "Zoom Sensor" (Wrist to Base Knuckle)
    palm_size = np.linalg.norm(base - wrist)

    # 4. Calculate the ratio (add tiny value to prevent division by zero)
    ratio = tip_to_wrist / (palm_size + 1e-6)

    return ratio # High value = Open, Low value = Curled



def take_snapshot (last_frame, state_name): 
    
    """
    I initialize my landmark_list at the top of the function because if  MediaPipe fails to find a hand in that specific snapshot,
    my  code might complain that landmark_list doesn't exist when it reaches the bottom print(landmark_list).
    """

    global is_frozen            
    landmark_list = []

    # I skipped the find_hands() because it was already called in the main loop

    # 1. Process the frame to find landmarks and draw the skeleton
    landmark_list = arinze_hand.find_position(last_frame, hand_indexes=[0], draw=False )

    trial_ratios = {} # Temporary Storage


    if landmark_list:
        print(f"\n ---- TRIAL {state_name.upper()} RATIOS ---- ")

        # This loop goes through MY FINGER_POINTS map
        for finger_name , points in FINGER_POINTS.items():

            ratio = get_finger_curl_ratio(landmark_list, tip_idx= points["tip"], base_idx= points["base"])

            # The ratios are stored and printed out one by one

            trial_ratios[finger_name] = round(ratio, 3)
            print(f'{finger_name} -> {trial_ratios[finger_name]}')


        print(landmark_list)

        # 2. Show the "Processed" frame (with the lines/dots)
        cv2.imshow("Image" , last_frame)

        print(f'ACCEPT these {state_name} values? Press \'y\' to SAVE OR \'n\' to THROW AWAY')
        
        while True:
            choice = cv2.waitKey(0) & 0xFF  # WAITING FOR KEY CONFIRMATION and  PAUSE here so you can actually see the result
            
            if choice == ord('y'):
                print(f'[OK] {state_name} CALIBRATION is now SAVED !!!!!!')
                print('SNAPSHOT PROCESSED. returning to Live feed...')

                is_frozen = False
                return trial_ratios # send back the verified data to be stored.

            elif choice == ord('n'):
                print(f'[DISCARDED] {state_name} CALIBRATION is THROWN AWAY !')
                is_frozen = False
                return None # sends back nothing
            
            else:
                print('Wrong Key pressed. Try Again') #  This only prints if you hit a key that isn't y or n

    else:
        print('No hand is detected. Returning to LIVE FEED. LANDMARK LIST IS EMPTY')
        is_frozen = False
        return None


"""
If you hit 'o' and the camera hasn't finished its "handshake" with your computer yet, frame will be its starting value of None. 
The code will see that, ignore your 'o' press, and print a message like "Camera warming up..." instead of crashing with a NoneType error.
"""

def print_both_calibra():

    print("\n" + "="*40)
    print("--------- OPEN AND CLOSED CURRENT CALIBRATION DATA --------")
    print('='*40)
    print(f"{'finger' : <10} | {'Open' : <10}' | {'close' : <10}" )
    print("-"* 40)
    
    for finger_name in FINGER_POINTS: # finger is only the key which is the finger name

        open_ratio = open_calibra.get(finger_name, None)
        close_ratio = close_calibra.get(finger_name, None)

        print(f'{finger_name:<10} | {open_ratio:<10} | {close_ratio:<10}')

    print('='*40 + "\n")

import math

# INITIAL SYSTEM RANGE SETTINGS ( baseline average ranges )
# The Dynamic Auto-Calibration Engine updates these dynamically in the background!
final_calibra = {
    "Thumb":  {"open": 1.15, "close": 0.50},
    "Index":  {"open": 1.25, "close": 0.45},
    "Middle": {"open": 1.30, "close": 0.45},
    "Ring":   {"open": 1.25, "close": 0.45},
    "Pinky":  {"open": 1.15, "close": 0.50},
}
calibra_done = True # Set to True by default so tracking starts INSTANTLY on run!

def calibrate_finger():
    global calibra_done

    if not open_calibra or not close_calibra:
        print('[WARNING] ERROR: I can\'t organise the data. One or Both calibration set are missing')
        return
    
    for finger_name in FINGER_POINTS: # finger is the finger name

        open_ratio = open_calibra[finger_name]
        close_ratio = close_calibra[finger_name]

        final_calibra[finger_name] = {'open': open_ratio, 'close' : close_ratio}

    calibra_done = True
    print('[OK] Finger calibration organized into final profile. calibra_done = TRUE ')

def normalize(current_ratio, limit_open, limit_close):

    norm = (current_ratio - limit_close ) / (limit_open - limit_close) # without the parenthesis, Python will divide limit_close / limit_open first, then subtract the rest, BECAUSE OF PEDMAS

    norm = float(np.clip(norm, 0.0, 1.0)) # The physical wall making norm stay btw 0.0 and 1.0
    return norm

# SERVO MAPPING    
SERVO_CONFIG = {
    "Thumb": {"min": 20, "max" : 150}, # these are stand in numbers till i physically tune the servos for each finger on my ar
    "Index": {"min": 20, "max": 160},
    "Middle": {"min": 20, "max": 160},
    "Ring": {"min": 25 , "max": 155},
    "Pinky": {"min": 25 , "max": 145},

}

def map_norm_to_servo_angle(norm, finger_name):

    servo_config = SERVO_CONFIG[finger_name]  
    servo_range = servo_config['max']  - servo_config['min']       # 1. Looking up the specific config for THIS finger
    servo_angle = servo_config['min'] + (norm * servo_range)

    servo_angle = round(float(servo_angle),1)

    return servo_angle

# SMOOTHENING (stops servo chatter)

class Smoother:

    def __init__(self, alpha=0.25): # I trust in the new data 25% and trust in the old data 75%

        self.alpha = alpha
        self.state = {}

    def smooth(self, finger_name, new_servo_angle): 

        if finger_name not in self.state: # if the finger is not in the dictionary cause it is not in a  positioned servo angle
            self.state[finger_name] = new_servo_angle # give it the new servo angle
        self.state[finger_name] = (self.alpha * new_servo_angle) + (1 - self.alpha) * (self.state[finger_name])
        return self.state[finger_name] # This returns the newly calculated, "filtered" angle to your main program


servo_smoother = Smoother(alpha=0.25) # Creating the EMA filter with alpha 0.25 (25% new, 75% old)

def get_wrist_angle(landmark_list):
    """
    Calculates the roll angle of the hand in degrees from 0 to 180,
    based on the vector between the wrist (0) and middle knuckle (9).
    """
    # 0 = Wrist, 9 = Middle Finger MCP
    w_x, w_y = landmark_list[0][1], landmark_list[0][2]
    m_x, m_y = landmark_list[9][1], landmark_list[9][2]
    
    dx = m_x - w_x
    dy = m_y - w_y # Screen Y coordinate increases downward
    
    # Calculate angle in degrees
    angle_rad = math.atan2(-dy, dx) # Invert dy to match standard Cartesian coords
    angle_deg = math.degrees(angle_rad)
    
    # Normally, straight hand is ~90. We map this directly to the Wrist servo (0 - 180)
    # Clamp to ensure it doesn't exceed mechanical boundaries
    wrist_servo = np.clip(angle_deg, 0.0, 180.0)
    return float(wrist_servo)

def full_realtime_process_pipeline(landmark_list):
    """
    The Assembly Line: Converts raw coordinates into smooth servo degrees : 
    RAW IMAGE -> AI LANDMARKS -> RATIO -> AUTO-CALIBRATION -> NORMALIZATION -> SERVO ANGLE -> SMOOTHENING
    """

    commands = {}

    # 1. Process all 5 fingers
    for finger_name, point in FINGER_POINTS.items():

        # Step 1: Get the raw ratio
        current_ratio = get_finger_curl_ratio(landmark_list, point['tip'], point['base'])

        # DYNAMIC AUTO-CALIBRATION (Learns your hand limits in real-time)
        if current_ratio > final_calibra[finger_name]['open']:
            final_calibra[finger_name]['open'] = current_ratio
        elif current_ratio < final_calibra[finger_name]['close']:
            final_calibra[finger_name]['close'] = current_ratio

        # Step 2: Normalize (Convert to 0.0 - 1.0 percentage) using self-adapting limits
        norm = normalize(current_ratio, final_calibra[finger_name]['open'] , final_calibra[finger_name]['close'])

        # Step 3: Map to Servo (Convert percentage to 20° - 160°)
        servo_angle = map_norm_to_servo_angle(norm, finger_name)

        # Step 4: Smooth (Remove the jitters using EMA)
        smooth_angle = servo_smoother.smooth(finger_name, servo_angle)

        # Step 5: Final Clean-up
        commands[finger_name] = round(float(smooth_angle),1)

    # 2. Process Wrist Roll!
    raw_wrist = get_wrist_angle(landmark_list)
    smooth_wrist = servo_smoother.smooth("Wrist", raw_wrist)
    commands["Wrist"] = round(float(smooth_wrist), 1)

    return commands


while True:
    landmark_list = [] # i initialize this here for defensive programming so that if in the future i ever want to use landmark_list outsid the 
    # if success function, my program won't crash because it wasn't initited due to if sucess not excuting.
    key = cv2.waitKey(1) & 0xFF # the 8 bit digit of the key that has been pressed is cut off from the rest and saved to 'key'
    
    if (key == ord('o') or key == ord('c')) and frame is None:
        print ('Camera is not ready yet. Wait a SEC')
        continue

    if not is_frozen:
        success, frame = cap.read() 
        if success:
            # ______________________PHASE 1: AI DETECTION _________________ 👐🏿👌🏿
            arinze_hand.find_hands(frame, draw=True)  
            landmark_list = arinze_hand.find_position(frame, draw= True)

            # _____________________PHASE 2: MY ROBOT CALIBRATION MATH (Awesomely designed by me) 🤖 ______________
            
            if landmark_list and calibra_done:
                # Run the entire assembly line
                servo_commands = full_realtime_process_pipeline(landmark_list)

                print(f'TRACKING: {servo_commands}', end='\r')
                send_to_virtual_hand(servo_commands)

            # --- I moved camera-dependent keys (which use or send 'frame') INSIDE success ---
            if key != 255:
                if key == ord('o'):
                    is_frozen = True
                    open_data = take_snapshot(frame, "open")
                    if open_data :
                        open_calibra = open_data

                elif key == ord('c'):
                        is_frozen = True 
                        close_data = take_snapshot(frame, "close")
                        if close_data:
                            close_calibra = close_data

                


            cv2.imshow("Image", frame) 

        # --- I am keeping non-camera keys (which don't use or send 'frame') OUTSIDE success ---

        if key != 255: # 255 signifies that a  key has NOT been pressed , while any number apart from 255 signifies a key has been pressed.
            if key == ord('s'):
                print_both_calibra()
                calibrate_finger()

                if calibra_done:
                    print(final_calibra)
                    print('SYSTEM READY FOR REAL TIME TRACKING')

                    
            elif key == ord('q'):
                break

            # checks for 'o' and 'c' errors ONLY if success was False
            elif (key == ord('o') or key == ord('c')) and (not success):
                print("[WARNING] Camera Error: Cannot take snapshot without a live frame!")

            else:
                # Now the "Wrong Key" only triggers for actual keyboard mistakes
                print(f'[WARNING] Wrong key pressed. The Key {chr(key)} is not a valid command (o,c,s,q). Try again ')



cap.release() #Shuts down the camera 
cv2.destroyAllWindows() # closes the GUI window





