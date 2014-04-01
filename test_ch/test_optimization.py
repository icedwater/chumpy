#!/usr/bin/env python
# encoding: utf-8
"""
Copyright (C) 2013
Author(s): Matthew Loper

See LICENCE.txt for licensing and contact information.
"""

import time
from numpy import *
import unittest
import chumpy as ch
from chumpy import Ch
import numpy as np
from scipy.optimize import rosen, rosen_der
from chumpy.utils import row, col


visualize = False


def Rosen():
    
    args = {
        'x1': Ch(-120.),
        'x2': Ch(-100.)
    }
    r1 = Ch(lambda x1, x2 : (x2 - x1**2.) * 10., args)
    r2 = Ch(lambda x1 : x1 * -1. + 1, args)

    func = [r1, r2]
    
    return func, [args['x1'], args['x2']]

class Madsen(Ch):
    dterms = ('x',)
    def compute_r(self):
        x1 = self.x.r[0]
        x2 = self.x.r[1]
        result = np.array((
            x1**2 + x2**2 + x1 * x2,
            np.sin(x1),
            np.cos(x2)
        ))
        return result
        
    def compute_dr_wrt(self, wrt):
        if wrt is not self.x:
            return None
        jac = np.zeros((3,2))
        x1 = self.x.r[0]
        x2 = self.x.r[1]
        jac[0,0] = 2. * x1 + x2
        jac[0,1] = 2. * x2 + x1
        
        jac[1,0] = np.cos(x1)
        jac[1,1] = 0
        
        jac[2,0] = 0
        jac[2,1] = -np.sin(x2)

        return jac
    

    def set_and_get_r(self, x_in):
        self.x = Ch(x_in)
        return col(self.r)
    
    def set_and_get_dr(self, x_in):
        self.x = Ch(x_in)
        return self.dr_wrt(self.x)




class RosenCh(Ch):
    dterms = ('x',)
    def compute_r(self):
        
        result = np.array((rosen(self.x.r) ))
        
        return result

    def set_and_get_r(self, x_in):
        self.x = Ch(x_in)
        return col(self.r)
    
    def set_and_get_dr(self, x_in):
        self.x = Ch(x_in)
        return self.dr_wrt(self.x).flatten()
    

    def compute_dr_wrt(self, wrt):
        if wrt is self.x:
            if visualize:
                import matplotlib.pyplot as plt
                residuals = np.sum(self.r**2)
                print '------> RESIDUALS %.2e' % (residuals,)
                print '------> CURRENT GUESS %s' % (str(self.x.r),)
                plt.figure(123)
                
                if not hasattr(self, 'vs'):
                    self.vs = []
                    self.xs = []
                    self.ys = []
                self.vs.append(residuals)
                self.xs.append(self.x.r[0])
                self.ys.append(self.x.r[1])
                plt.clf();
                plt.subplot(1,2,1)
                plt.plot(self.vs)
                plt.subplot(1,2,2)
                plt.plot(self.xs, self.ys)
                plt.draw()


            return row(rosen_der(self.x.r))
    


class TestOptimization(unittest.TestCase):

    def test_dogleg_rosen(self):
        obj, freevars = Rosen()
        ch.minimize(fun=obj, x0=freevars, method='dogleg', options={'maxiter': 337})
        self.assertTrue(freevars[0].r[0]==1.)
        self.assertTrue(freevars[1].r[0]==1.)

    def test_dogleg_madsen(self):
        obj = Madsen(x = Ch(np.array((3.,1.))))
        ch.minimize(fun=obj, x0=[obj.x], method='dogleg', options={'maxiter': 34})
        self.assertTrue(np.sum(obj.r**2)/2 < 0.386599528247)
        
    @unittest.skip('negative sign in exponent screws with reverse mode')
    def test_bfgs_rosen(self):
        from optimization import minimize_bfgs_lsq        
        obj, freevars = Rosen()        
        minimize_bfgs_lsq(obj=obj, niters=421, verbose=False, free_variables=freevars)        
        self.assertTrue(freevars[0].r[0]==1.)
        self.assertTrue(freevars[1].r[0]==1.)

    def test_bfgs_madsen(self):
        from chumpy import SumOfSquares      
        import scipy.optimize
        obj = Ch(lambda x : SumOfSquares(Madsen(x = x)) )
        
        def errfunc(x):
            obj.x = Ch(x)
            return obj.r
        
        def gradfunc(x):
            obj.x = Ch(x)
            return obj.dr_wrt(obj.x).ravel()
        
        x0 = np.array((3., 1.))

        # Optimize with built-in bfgs.
        # Note: with 8 iters, this actually requires 14 gradient evaluations.
        # This can be verified by setting "disp" to 1.
        #tm = time.time()
        x1 = scipy.optimize.fmin_bfgs(errfunc, x0, fprime=gradfunc, maxiter=8, disp=0)
        #print 'forward: took %.es' % (time.time() - tm,)
        self.assertTrue(obj.r/2. < 0.386599528247)

        # Optimize with chumpy's minimize (which uses scipy's bfgs).
        obj.x = x0
        ch.minimize(fun=obj, x0=[obj.x], method='bfgs', options={'maxiter': 8})
        self.assertTrue(obj.r/2. < 0.386599528247)


suite = unittest.TestLoader().loadTestsFromTestCase(TestOptimization)

if __name__ == '__main__':
    
    if False: # show rosen 
        import matplotlib.pyplot as plt
        visualize = True
        plt.ion()
        unittest.main()
        import pdb; pdb.set_trace()
    else:
        unittest.main()
