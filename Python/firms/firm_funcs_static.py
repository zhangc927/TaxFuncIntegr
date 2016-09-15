'''
------------------------------------------------------------------------
This script contains functions common to the SS and TP solutions for the 
OG model with S-period lived agents, exogenous labor, and M industries and I goods.
    get_p
    get_p_tilde
    get_c_tilde
    get_c
    get_C
    get_K
    get_L
    get_b_errors
------------------------------------------------------------------------
'''
# Import Packages
import numpy as np
import scipy.optimize as opt
import ssfuncs_static as ssf
reload(ssf)
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
from mpl_toolkits.mplot3d import Axes3D
import sys

'''
------------------------------------------------------------------------
    Functions
------------------------------------------------------------------------
'''

def get_p(params, r, w):
    '''
    Generates time path of industry prices p_m from r_path and w_path

    Inputs:
        params = length 4 tuple, (A, gamma, epsilon, delta)
        A   = [M,T+S-2] matrix, total factor productivity for each
                 industry
        gamma = [M,T+S-2] matrix, capital share of income for each industry
        epsilon = [M,T+S-2] matrix, elasticity of substitution between capital
                 and labor for each industry
        delta = [M,T+S-2] matrix, capital depreciation rate for each
                 industry
        r  = [T+S-2,] matrix, time path of interest rate
        w      = [T+S-2,] matrix, time path of wage

    Functions called: None

    Objects in function:
        p = [M, T+S-2] matrix, time path of industry prices

    Returns: p
    '''
    A, gamma, epsilon, delta = params

    p = (1 / A) * ((gamma * ((r + delta) **
                   (1 - epsilon)) + (1 - gamma) * (w **
                   (1 - epsilon))) ** (1 / (1 - epsilon)))

    return p

def get_p_tilde(alpha, p_c):
    '''
    Generates time path of composite price p from p_path

    Inputs:
        alpha = [I, T+S-2], expenditure share on each good along time path
        p_c = [I, T+S-2] matrix, time path of industry prices

    Functions called: None

    Objects in function:
        p_tilde = [T+S-2,] vector, time path of price of composite good

    Returns: p_tilde
    '''

    p_tilde = ((p_c/alpha)**alpha).prod(axis=0)
    return p_tilde


def get_c_tilde(c_bar, r, w, p_c, p_tilde, n, b):
    '''
    Generates vector of remaining lifetime consumptions from individual
    savings, and the time path of interest rates and the real wages

    Inputs:
        u      = (not an input, but relevant),integer in [2,80], number 
                  of periods remaining in individual life
        r  = [u,] vector, remaining interest rates
        w  = [u,] vector, remaining wages
        p_c = [I, u] matrix, remaining industry prices
        p_tilde  = [u,] vector, remaining composite prices
        n   = [u,] vector, remaining exogenous labor supply
        b   = [u,] vector, remaining savings including initial
                 savings

    Functions called: None

    Objects in function:
        c_cstr = [u,] boolean vector, =True if element c_s <= 0
        b_s    = [u,] vector, b
        b_sp1  = [u,] vector, last p-1 elements of b and 0 in last
                 element
        c   = [u,] vector, remaining consumption by age c_s

    Returns: c, c_constr
    '''

    if np.isscalar(b): # check if scalar - if so, then in last period of life and savings = 0
        c_tilde = (1 / p_tilde) *((1 + r) * b + w * n -
           (p_c * c_bar).sum(axis=0))
        c_tilde_cstr = c_tilde <= 0
    else:
        b_s = b
        b_sp1 = np.append(b[1:], [0])
        c_tilde = (1 / p_tilde) *((1 + r) * b_s + w * n -
           (p_c * c_bar).sum(axis=0) - b_sp1)
        c_tilde_cstr = c_tilde <= 0

    return c_tilde, c_tilde_cstr


def get_c(alpha, c_bar, c_tilde, p_c, p_tilde):
    '''
    Generates matrix of remaining lifetime consumptions of individual
    goods

    Inputs:
        u      = (not an input, but relevant) integer in [2,80], number 
                 of periods remaining in individual life
        alpha  = [I,u] vector, remaining expenditure shares on consumption goods
        c_tilde =[u,] vector, remaining composite consumption amounts
        p_c    = [I, u] matrix, remaining consumption good prices
        c_bar    = [I, u] matrix, remaining minimum consumption amounts
        p_tilde  = [u,] vector, remaining composite prices

    Functions called: None

    Objects in function:
        c   = [I,u] vector, remaining consumption by age c_s

    Returns: c, c_constr
    '''

    c = alpha * ((p_tilde * c_tilde) / p_c) + c_bar

    c_cstr = c <= 0
    return c, c_cstr


def get_C(c):
    '''
    Generates vector of aggregate consumption C_{i} of good i

    Inputs:
        c = [S, S+T-1, I] array, time path of distribution of
                 individual consumption of each good c_{i,s,t}

    Functions called: None

    Objects in function:
        C = [I,S+T-1] matrix, aggregate consumption of all goods

    Returns: C
    '''

    C = (c.sum(axis=0)).transpose()

    return C


def get_K(r, w, X, A, gamma, epsilon, delta):
    '''
    Generates vector of capital demand from production industry m 
    along the time path for a given X, r, w.

    Inputs:
        r      = [T,] vector, real interest rates
        w      = [T,] vector, real wage rates
        X  = [M,T] matrix, output from each industry
        A       = [M,T] matrix, total factor productivity values for all
                   industries
        gamma = [M,T] matrix, capital shares of income for all
                 industries
        epsilon = [M,T] matrix, elasticities of substitution between
                 capital and labor for all industries
        delta = [M,T] matrix, model period depreciation rates for all
                 industries

    Functions called: None

    Objects in function:
        aa    = [M,T] matrix, gamma
        bb    = [M,T] matrix, 1 - gamma
        cc    = [M,T] matrix, (1 - gamma) / gamma
        dd    = [M,T] matrix, (r + delta) / w
        ee    = [M,T] matrix, 1 / epsilon
        ff    = [M,T] matrix, (epsilon - 1) / epsilon
        gg    = [M,T] matrix, epsilon - 1
        hh    = [M,T] matrix, epsilon / (1 - epsilon)
        ii    = [M,T] matrix, ((1 / A) * (((aa ** ee) + (bb ** ee) *
                (cc ** ff) * (dd ** gg)) ** hh))
        K_path = [M,T] matrix, capital demand of all industries

    Returns: K_path
    '''
    aa = gamma
    bb = 1 - gamma
    cc = (1 - gamma) / gamma
    dd = (r + delta) / w
    ee = 1 / epsilon
    ff = (epsilon - 1) / epsilon
    gg = epsilon - 1
    hh = epsilon / (1 - epsilon)

    K = ((X / A) *
         (((aa ** ee) + (bb ** ee) * (cc ** ff) * (dd ** gg)) ** hh))

    return K



def get_L(r, w, K, gamma, epsilon, delta):
    '''
    Generates vector of labor demand L_{m} for good m given X_{m}, p_{m}, r and w

    Inputs:
        K = [M, T] matrix, time path of aggregate output by
                 industry
        r  = [T, ] matrix, time path of real interest rate
        w  = [T, ] matrix, time path of real wage
        gamma = [M,T] matrix, capital shares of income for all
                 industries
        epsilon = [M,T] matrix, elasticities of substitution between
                 capital and labor for all industries
        delta = [M,T] matrix, rate of phyical depreciation for all industries

    Functions called: None

    Objects in function:
        L = [M,T] matrix, labor demand from each industry

    Returns: L_path
    '''
    L = K*((1-gamma)/gamma)*(((r+delta)/w)**epsilon)

    return L

def get_b_errors(params, r, c_tilde, c_tilde_cstr, diff):
    '''
    Generates vector of dynamic Euler errors that characterize the
    optimal lifetime savings

    Inputs:
        params = length 2 tuple, (beta, sigma)
        beta   = scalar in [0,1), discount factor
        sigma  = scalar > 0, coefficient of relative risk aversion
        r      = scalar > 0, interest rate
        c_tilde   = [S,] vector, distribution of consumption by age c_s
        c_tilde_cstr = [S,] boolean vector, =True if c_s<=0 for given b
        diff   = boolean, =True if use simple difference Euler errors.
                 Use percent difference errors otherwise.

    Functions called: None

    Objects in function:
        mu_c     = [S-1,] vector, marginal utility of current
                   consumption
        mu_cp1   = [S-1,] vector, marginal utility of next period
                   consumption
        b_errors = [S-1,] vector, Euler errors with errors = 0
                   characterizing optimal savings b

    Returns: b_errors
    '''
    beta, sigma = params
    c_tilde[c_tilde_cstr] = 9999. # Each consumption must be positive to
                         # generate marginal utilities
    mu_c = c_tilde[:-1] ** (-sigma)
    mu_cp1 = c_tilde[1:] ** (-sigma)
    if diff == True:
        b_errors = (beta * (1 + r) * mu_cp1) - mu_c
        b_errors[c_tilde_cstr[:-1]] = 9999.
        b_errors[c_tilde_cstr[1:]] = 9999.
    else:
        b_errors = ((beta * (1 + r) * mu_cp1) / mu_c) - 1
        b_errors[c_tilde_cstr[:-1]] = 9999. / 100
        b_errors[c_tilde_cstr[1:]] = 9999. / 100
    return b_errors


