
import cv2

def my_cornerRect(frame, bbox, l=30, t=5, color=(255,0,255)):
    """
    Draws a high-tech corner-only rectangle.
    :param frame: The image/frame to draw on.
    :param bbox: A tuple/list (x, y, w, h).
    :param l: Length of the corner lines.
    :param t: Thickness of the lines.
    :param color: BGR color tuple.
    :return: The frame with the drawing.
    """
    x,y,w,h = bbox
    x1,y1 = x+w, y+h

    # Top left Corner
    cv2.line(frame, (x,y), (x+l,y), color,t) # Horizontal part
    cv2.line(frame, (x,y), (x,y+l), color,t) # Vertical part

    # Top Right Corner

    cv2.line(frame, (x1,y), (x1-l,y), color,t) # Horizontal part
    cv2.line(frame, (x1,y), (x1,y+l), color,t) # Vertical part

    # Bottom Left Corner

    cv2.line(frame, (x,y1), (x+l,y1), color,t) # Horizontal part
    cv2.line(frame, (x,y1), (x,y1-l), color,t) # Vertical part

    # Bottom Right Corner

    cv2.line(frame, (x1,y1), (x1-l,y1), color, t) # Horizontal part
    cv2.line(frame, (x1,y1), (x1, y1-l), color, t) # Vertical part

    return frame