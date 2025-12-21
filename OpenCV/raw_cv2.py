
import cv2

def my_cornerRect(frame, bbox, l=30, t=5,rect_t = 1, corner_color=(255,0,255), rect_color=(0,255,0)): 
    """
    Draws a high-tech corner-only rectangle.
    :param frame: The image/frame to draw on.
    :param bbox: A tuple/list (x, y, w, h).
    :param l: Length of the corner lines.
    :param t: Thickness of the lines.
    :param corner_color: BGR corner_color tuple.
    rect_color -> the color of the main rectangle
    rect_t -> the thickness of the main rectangle
    :return: The frame with the drawing.
    """
    x,y,w,h = bbox
    x1,y1 = x+w, y+h

    # Top left Corner
    cv2.line(frame, (x,y), (x+l,y), corner_color,t) # Horizontal part
    cv2.line(frame, (x,y), (x,y+l), corner_color,t) # Vertical part

    # Top Right Corner

    cv2.line(frame, (x1,y), (x1-l,y), corner_color,t) # Horizontal part
    cv2.line(frame, (x1,y), (x1,y+l), corner_color,t) # Vertical part

    # Bottom Left Corner

    cv2.line(frame, (x,y1), (x+l,y1), corner_color,t) # Horizontal part
    cv2.line(frame, (x,y1), (x,y1-l), corner_color,t) # Vertical part

    # Bottom Right Corner

    cv2.line(frame, (x1,y1), (x1-l,y1), corner_color, t) # Horizontal part
    cv2.line(frame, (x1,y1), (x1, y1-l), corner_color, t) # Vertical part

    # Time for the main Rectangle

    cv2.line(frame,(x+l,y), (x1-l,y), rect_color, rect_t) # Top
    cv2.line(frame,(x+l,y1),(x1-l,y1), rect_color, rect_t) # Bottom
    
    cv2.line(frame,(x,y+l), (x,y1-l), rect_color, rect_t) # Side 1
    cv2.line(frame, (x1,y+l), (x1,y1-l), rect_color, rect_t) # Side 2
    return frame