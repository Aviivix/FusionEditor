from math import sqrt, pow, sin, cos
from math import pi as m_pi

m_pi_2 = m_pi * 2

# original c code:
# https://raw.githubusercontent.com/warrenm/AHEasing/master/AHEasing/easing.c
# Copyright (c) 2011, Auerhaus Development, LLC
# http://sam.zoy.org/wtfpl/COPYING for more details.
# python code:
# https://gist.github.com/zeffii/c1e14dd6620ad855d81ec2e89a859719


#  Modeled after the line y = x
def linear(p):
    return p


# Modeled after the parabola y = x^2
def quad_in(p):
    return p * p


# Modeled after the parabola y = -x^2 + 2x
def quad_out(p):
    return -(p * (p - 2))


# Modeled after the piecewise quadratic
# y = (1/2)((2x)^2)             ; [0, 0.5)
# y = -(1/2)((2x-1)*(2x-3) - 1) ; [0.5, 1]
def quad(p):
    if p < 0.5:
        return 2 * p * p
    return (-2 * p * p) + (4 * p) - 1


# Modeled after the cubic y = x^3
def cub_in(p):
    return p * p * p


# Modeled after the cubic y = (x - 1)^3 + 1
def cub_out(p):
    f = (p - 1)
    return f * f * f + 1


# Modeled after the piecewise cubic
# y = (1/2)((2x)^3)       ; [0, 0.5)
# y = (1/2)((2x-2)^3 + 2) ; [0.5, 1]
def cub(p):
    if p < 0.5:
        return 4 * p * p * p
    else:
        f = ((2 * p) - 2)
        return 0.5 * f * f * f + 1


# Modeled after the quartic x^4
def quart_in(p):
    return p * p * p * p


# Modeled after the quartic y = 1 - (x - 1)^4
def quart_out(p):
    f = (p - 1)
    return f * f * f * (1 - p) + 1


# Modeled after the piecewise quartic
# y = (1/2)((2x)^4)        ; [0, 0.5)
# y = -(1/2)((2x-2)^4 - 2) ; [0.5, 1]
def quart(p):
    if p < 0.5:
        return 8 * p * p * p * p
    else:
        f = (p - 1)
        return -8 * f * f * f * f + 1


# Modeled after the quintic y = x^5
def quint_in(p):
    return p * p * p * p * p


# Modeled after the quintic y = (x - 1)^5 + 1
def quint_out(p):
    f = (p - 1)
    return f * f * f * f * f + 1


# Modeled after the piecewise quintic
# y = (1/2)((2x)^5)       ; [0, 0.5)
# y = (1/2)((2x-2)^5 + 2) ; [0.5, 1]
def quint(p):
    if p < 0.5:
        return 16 * p * p * p * p * p
    else:
        f = ((2 * p) - 2)
        return 0.5 * f * f * f * f * f + 1


# Modeled after quarter-cycle of sine wave
def sine_in(p):
    return sin((p - 1) * m_pi_2) + 1


# Modeled after quarter-cycle of sine wave (different phase)
def sine_out(p):
    return sin(p * m_pi_2)


# Modeled after half sine wave
def sine(p):
    return 0.5 * (1 - cos(p * m_pi))


# Modeled after shifted quadrant IV of unit circle
def circ_in(p):
    return 1 - sqrt(1 - (p * p))


# Modeled after shifted quadrant II of unit circle
def circ_out(p):
    return sqrt((2 - p) * p)


# Modeled after the piecewise circular function
# y = (1/2)(1 - sqrt(1 - 4x^2))           ; [0, 0.5)
# y = (1/2)(sqrt(-(2x - 3)*(2x - 1)) + 1) ; [0.5, 1]
def circ(p):
    if p < 0.5:
        return 0.5 * (1 - sqrt(1 - 4 * (p * p)))
    else:
        return 0.5 * (sqrt(-((2 * p) - 3) * ((2 * p) - 1)) + 1)


# Modeled after the exponential function y = 2^(10(x - 1))
def exp_in(p):
    return p if (p == 0.0) else pow(2, 10 * (p - 1))


# Modeled after the exponential function y = -2^(-10x) + 1
def exp_out(p):
    return p if (p == 1.0) else 1 - pow(2, -10 * p)


# Modeled after the piecewise exponential
# y = (1/2)2^(10(2x - 1))         ; [0,0.5)
# y = -(1/2)*2^(-10(2x - 1))) + 1 ; [0.5,1]
def exp(p):
    if p == 0.0 or p == 1.0:
        return p

    if p < 0.5:
        return 0.5 * pow(2, (20 * p) - 10)
    else:
        return -0.5 * pow(2, (-20 * p) + 10) + 1


# Modeled after the damped sine wave y = sin(13pi/2*x)*pow(2, 10 * (x - 1))
def elast_in(p):
    return sin(13 * m_pi_2 * p) * pow(2, 10 * (p - 1))


# Modeled after the damped sine wave y = sin(-13pi/2*(x + 1))*pow(2, -10x) + 1
def elast_out(p):
    return sin(-13 * m_pi_2 * (p + 1)) * pow(2, -10 * p) + 1


# Modeled after the piecewise exponentially-damped sine wave:
# y = (1/2)*sin(13pi/2*(2*x))*pow(2, 10 * ((2*x) - 1))      ; [0,0.5)
# y = (1/2)*(sin(-13pi/2*((2x-1)+1))*pow(2,-10(2*x-1)) + 2) ; [0.5, 1]
def elast(p):
    if p < 0.5:
        return 0.5 * sin(13 * m_pi_2 * (2 * p)) * pow(2, 10 * ((2 * p) - 1))
    else:
        return 0.5 * (sin(-13 * m_pi_2 * ((2 * p - 1) + 1)) * pow(2, -10 * (2 * p - 1)) + 2)


# Modeled after the overshooting cubic y = x^3-x*sin(x*pi)
def back_in(p):
    return p * p * p - p * sin(p * m_pi)


# Modeled after overshooting cubic y = 1-((1-x)^3-(1-x)*sin((1-x)*pi))
def back_out(p):
    f = (1 - p)
    return 1 - (f * f * f - f * sin(f * m_pi))


# Modeled after the piecewise overshooting cubic function:
# y = (1/2)*((2x)^3-(2x)*sin(2*x*pi))           ; [0, 0.5)
# y = (1/2)*(1-((1-x)^3-(1-x)*sin((1-x)*pi))+1) ; [0.5, 1]
def back(p):
    if p < 0.5:
        f = 2 * p
        return 0.5 * (f * f * f - f * sin(f * m_pi))
    else:
        f = (1 - (2 * p - 1))
        return 0.5 * (1 - (f * f * f - f * sin(f * m_pi))) + 0.5


def bounce_in(p):
    return 1 - bounce_out(1 - p)


def bounce_out(p):
    if p < 4 / 11.0:
        return (121 * p * p) / 16.0

    elif p < 8 / 11.0:
        return (363 / 40.0 * p * p) - (99 / 10.0 * p) + 17 / 5.0

    elif p < 9 / 10.0:
        return (4356 / 361.0 * p * p) - (35442 / 1805.0 * p) + 16061 / 1805.0

    else:
        return (54 / 5.0 * p * p) - (513 / 25.0 * p) + 268 / 25.0


def bounce(p):
    if p < 0.5:
        return 0.5 * bounce_in(p * 2)
    else:
        return 0.5 * bounce_out(p * 2 - 1) + 0.5
