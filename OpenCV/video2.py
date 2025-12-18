import cv2

cap = cv2.VideoCapture(0) 

while True:
    sucess, frame = cap.read() 
    if sucess:
        cv2.imshow("Image", frame) 
    print(frame.shape)
    cv2.waitKey(0) 

'''
cap.release() #Shuts down the camera 
cv2.destroyAllWindows() # closes the GUI window
'''

