"""handy trigonometry computations"""
import math

def compute_angle(A, B):
    """compute the angle between the x axis and the line between A and B"""
    x_A, y_A = A
    x_B, y_B = B
    if x_A == x_B:
        angle_ab = math.pi/2 if y_A < y_B else - math.pi/2
    elif y_A == y_B:
        angle_ab = 0 if x_A < x_B else math.pi
    else:
        angle_ab = math.atan((y_A - y_B)/(x_A - x_B ))
    return angle_ab

def compute_arrow_points(A, B, radius = 10):
    """compute the two points the arrow "line" should be located at the end
    of the arrow"""
    angle_ab = compute_angle(A, B)
    x_B, y_B = B

    x_C = x_B - math.cos(angle_ab + math.pi/4) * radius
    y_C = y_B - math.sin(angle_ab + math.pi/4) * radius


    x_D = x_B - math.cos(angle_ab - math.pi/4) * radius
    y_D = y_B - math.sin(angle_ab - math.pi/4) * radius

    return (x_C, y_C), (x_D, y_D)
