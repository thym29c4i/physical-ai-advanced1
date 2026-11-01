import math

GOALS = {'reception': (2.5, 0.0), 'warehouse': (0.0, 2.5), 'workshop': (-2.5, 0.0), 'home': (0.0, 0.0)}


def velocity(x, y, yaw, target):
    dx, dy = target[0]-x, target[1]-y
    distance = math.hypot(dx, dy)
    if distance < 0.18:
        return 0.0, 0.0, True
    error = math.atan2(math.sin(math.atan2(dy, dx)-yaw), math.cos(math.atan2(dy, dx)-yaw))
    angular = max(-0.8, min(0.8, 1.8*error))
    linear = min(0.35, 0.65*distance) if abs(error) < 0.35 else 0.0
    return linear, angular, False
