from numpy import array

#Returns n composite Gauss-Legendre points on the interval [0,1]
#Options: flag not given: return points on the interval with singularity at 0
#         flag = 1 return points on the interval with singularity at t
#         flag = 2 return points on the interval with singularity at t, 
#                  where it is assumed that the function is zero at
#                  times smaller than t
def sing_gauleg(n, **kwargs):
    x,w = array(cgauleg(n))
    if 't' in kwargs:
	t = kwargs['t']
        assert 'flag' in kwargs  #if t is given flag must be set
	flag = kwargs['flag']
    else:
	return x,w
    x *= -1
    x += 1
    x *= t
    w *= t
    if flag == 2 or t == 1.:
	assert t != 0
        return x,w
    x1,w1 = array(cgauleg(n))
    x1 *= (1-t)
    x1 += t
    w1 *= (1-t)
    from numpy import hstack
    x = hstack([x,x1])
    w = hstack([w,w1])
    return x,w

from numpy import empty, sqrt
from memoize import memoize

#Returns composite Gauss-Legendre points on [0,1]
@memoize
def cgauleg(n):
    sigma = (sqrt(2)-1)**2    # parameter of geometric subdivision
    x = empty([(n*(n+3))/2-1])
    w = empty([(n*(n+3))/2-1])

    xl = sigma
    xr = 1.
    cnt = 0
    for j in range(n-1):
        nj = n-j     
        x1,w1 = gauleg(nj)
        x1 = xl+(xr-xl)*x1
        w1=(xr-xl)*w1
        x[cnt:cnt+nj]= x1[0:nj]
        w[cnt:cnt+nj] = w1[0:nj]
        xr=xl
        xl=xl*sigma
        cnt += nj 
    nj = n
    x1,w1 = array(gauleg(nj))
    x1=xr*x1
    w1=xr*w1
    x[cnt:cnt+nj] = x1[0:nj]
    w[cnt:cnt+nj] = w1[0:nj]
    return (x,w)
   
from numpy import cos, pi

#Gauss-legendre points and weights in the interval [0,1]. 
@memoize 
def gauleg(n):
    x = empty([n]);    w = empty([n])
    m = int((n+1)/2)
    xm = 0.0;    xl = 1.0
    for i in range(m):
        z=cos(pi*(i+1-0.25)/(n+0.5))
        while True:
            p1=1.0
            p2=0.0
            for j in range(n):
                p3=p2
                p2=p1
                p1=((2.0*j+1.0)*z*p2-j*p3)/(j+1)
            pp=n*(z*p1-p2)/(z*z-1.0)
            z1=z
            z=z1-p1/pp
	    from numpy import finfo
            if abs(z-z1) < finfo(float).eps:
                break
            x[i]=xm-xl*z
        x[n-1-i]=xm+xl*z
        w[i]=2.0*xl/((1.0-z*z)*pp*pp)
        w[n-1-i]=w[i]
    x = (x+1.)/2.
    w = w/2.
    return x, w

