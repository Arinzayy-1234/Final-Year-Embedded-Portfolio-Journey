import cv2

cap = cv2.VideoCapture(0) 

while True:
    sucess, frame = cap.read() 
    if sucess:
        cv2.imshow("Image", frame) 
    print(frame.shape)
    #stops the loop is 'q' is pressed
    # cv2.waitKey(1) waits 1ms and returns the jey pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release() #Shuts down the camera 
cv2.destroyAllWindows() # closes the GUI window

'''Note: When the video window pops up, make sure you click on it with your mouse before pressing 'q' 
so the computer knows you are talking to that window!
Otherwise, it may not register your key press.
'''