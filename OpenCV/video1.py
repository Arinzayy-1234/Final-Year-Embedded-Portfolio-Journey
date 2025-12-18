import cv2

cap = cv2.VideoCapture(0) #what does videoCapture(0) do ?

while True:
    sucess, frame = cap.read() # This is reading from the webcam. What is sucess and frame ?
    cv2.imshow("Image", frame) # is imshow a method of class cv2? # This is showing our image. What does the imshow() do ?
    cv2.waitKey(1) #this is giving a delay of 1 miliseccond , what does the waitkey method do ?
    