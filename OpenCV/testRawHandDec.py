import cv2
from  rawMp import RawHandDetector

cap = cv2.VideoCapture(0) 

arinze_hand = RawHandDetector()

while True:
    sucess, frame = cap.read() 
    if sucess:
        frame = arinze_hand.find_hands(frame)
        cv2.imshow("Image", frame) 
        print(arinze_hand.find_position(frame)) 

    #stops the loop is 'q' is pressed
    # cv2.waitKey(1) waits 1ms and returns the key pressed
    if cv2.waitKey(0) & 0xFF == ord('q'):
        break

cap.release() #Shuts down the camera 
cv2.destroyAllWindows() # closes the GUI window

