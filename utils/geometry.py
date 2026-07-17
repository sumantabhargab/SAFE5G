"""
====================================================
Geometry Utilities
====================================================
"""

import math


def distance(p1, p2):

    return math.sqrt(

        (p1[0] - p2[0]) ** 2 +

        (p1[1] - p2[1]) ** 2

    )


def midpoint(p1, p2):

    return (

        (p1[0] + p2[0]) // 2,

        (p1[1] + p2[1]) // 2

    )


def inside_radius(p1, p2, radius):

    return distance(p1, p2) <= radius