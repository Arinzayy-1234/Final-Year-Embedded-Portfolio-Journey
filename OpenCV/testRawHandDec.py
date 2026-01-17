import cv2
from  rawMp import RawHandDetector

cap = cv2.VideoCapture(0) 

arinze_hand = RawHandDetector()

while True:
    success, frame = cap.read() 
    if success:
        frame = arinze_hand.find_hands(frame, draw=True)
        print(arinze_hand.find_position(frame,  hand_indexes= [0,], draw=True)) 
        cv2.imshow("Image", frame) 

    #stops the loop is 'q' is pressed
    # cv2.waitKey(1) waits 1ms and returns the key pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release() #Shuts down the camera 
cv2.destroyAllWindows() # closes the GUI window

