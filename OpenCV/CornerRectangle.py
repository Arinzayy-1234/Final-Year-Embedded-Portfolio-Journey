import cv2 
from raw_cv2 import my_cornerRect 

cap = cv2.VideoCapture(0) 

def main():
    while True:
        sucess, frame = cap.read() 
        if sucess:
            # cv2.rectangle(frame, (200,200), (500,400)) <- instead of using this 

            # Define a sample Bounding Box (x, y, width, height)
            # In the future, these values will come from Mediapipe!
            my_cornerRect(frame, (200,200,300,200)) 
            cv2.imshow("Image", frame) 
        
        #stops the loop is 'q' is pressed
        # cv2.waitKey(1) waits 1ms and returns the jey pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release() #Shuts down the camera 
    cv2.destroyAllWindows() # closes the GUI window

if __name__ == "__main__":
    main()