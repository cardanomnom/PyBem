from numpy import empty, tile
from numpy import sum, cumsum, prod, ix_, hsplit, hstack, vstack
from numpy import log
from memoize import memoize
from integrate1d import r_jaclog, gauss, gauleg, cgauleg, sing_gauleg, sing_gauleg2

#Integrates the function f over the domains specified
#by projs, the optional arguments specify number of quadrature points
#and where the singularity is located,
#if empty it is assumed f is non-singular
def integrate(f, *projs, **kwargs):
    n = kwargs['n']  #number of quadrature points in regular directions
    #if number of points in singular direction is not specified use 18
    if 'nsing' in kwargs:
        nsing = kwargs['nsing']
    else:
       nsing = 18
    def g(*ths):
        return ( f (*(p(th) for p,th in zip(projs,ths)))
               * prod([p.derivative(th) for p,th in zip(projs,ths)], axis=0)
               )
    dims = tuple(p.dim for p in projs)
    if 't' in kwargs:
        if 'x' in kwargs:
            return integrate_on_0_1(g, SingXT((nsing,dims,kwargs['x'],kwargs['t'])))
        return integrate_on_0_1(g, SingT((nsing, dims, kwargs['t'])))
    return integrate_on_0_1(g, gaulegs((n, dims)))

#integrate over the unit simplex
from integrate1d import GJquad
def GJTria(f,n):
    xi,wxi   = GJquad(0,0,n)
    eta,weta = GJquad(1,0,n)
    z,wz = tensor((xi,wxi),(eta,weta))

    z[:,0] = (1.+z[:,0])*(1-z[:,1])/4.
    z[:,1] = (1.+z[:,1])/2.
    return sum(f(z[:,0],z[:,1])*wz/8.)

def createQuadRule(dims, r1, r2):
    #assert sum(r1[1]) > 0.1
    #assert sum(r2[1]) > 0.1
    d = sum(dims)
    X,W = r1
    for i in range(d-1):
       X,W = tensor((X,W), r2)
    Xs = hsplit(X, cumsum(dims[:-1]))
    return (Xs, W.reshape(-1,1))

def integrate_on_0_1(f, (Xs,W)):
    return sum(f(*Xs)*W)

#The tensor product of two one dimensional quadrature rules
def tensor((X1,W1), (X2,W2)):
    d = 2
    X = empty([len(X1),len(X2), d])
    for i, a in enumerate(ix_(X1,X2)):
        X[...,i] = a
    X = X.reshape(-1, d)

    W = tile(1.0, [len(W1),len(W2)])

    for a in ix_(W1,W2):
        W[...] *= a

    W = W.reshape(1, -1)  # Need this format to avoid tranposing in all the other routines

    return X,W


#Routine plots the quadrature points
from matplotlib.pyplot import figure
def plot(x,w):
    f = figure()
    if isinstance(x, tuple) and len(x) == 2:
        f.gca().plot(x[0],x[1],'o')
    elif len(x.shape) == 1:
        f.gca().vlines(x,[0],w)
        #f.gca().plot(x,zeros(x.size),'o')
        #f.gca().plot(x,w,'x')
    elif x.shape[1] == 2:
        f.gca().plot(x[:,0],x[:,1],'o')
    else:
        raise RuntimeError("Can't plot quadrature points with shape {}.".format(x.shape))
    f.show()

def SingXT((n,dims,x,t)):
    return createQuadRule(dims, sing_gauleg2(n,x), sing_gauleg(n,t))

def SingT((n,dims,t)):
    return createQuadRule(dims, gauleg(n), sing_gauleg(n,t))
@memoize
def gaulegs((n,dims)):
    return createQuadRule(dims, gauleg(n), gauleg(n))

@memoize
def SingLogDiag( n ):
    abl    = r_jaclog(n,0)
    X,W = tensor(gauss(n,abl), gauleg(n))
    X0 = hstack([ (1-X[:,0])*X[:,1], (1-X[:,1])*X[:,0], X[:,1]+X[:,0]*(1-X[:,1]), 1-X[:,0]+X[:,1]*X[:,0] ])
    X1 = hstack([ X[:,1]           , X[:,0]           , X[:,1]                  , 1-X[:,0] ])
    Wn = hstack([ X[:,1]*W         , X[:,0]*W         , (1-X[:,1])*W            , X[:,0]*W ])
    return ((X0.reshape(-1,1),X1.reshape(-1,1)), Wn.reshape(-1,1))

@memoize
def SingLogLeftupper( n ):
    abl    = r_jaclog(n,0)
    X,W = tensor(gauss(n,abl), gauleg(n))
    X2,W2 = tensor(gauleg(n), gauleg(n))
    X0 = hstack([X[:,0]*X[:,1] , X2[:,0]*X2[:,1]           , X[:,0]                 , X2[:,0]])
    X1 = hstack([1-X[:,0]      , 1-X2[:,0]                 , X[:,0]*X[:,1]+1-X[:,0] , X2[:,1]*X2[:,0]+1-X2[:,0]])
    Wn = hstack([X[:,0]*W      ,-X2[:,0]*log(X2[:,1]+1)*W2 , X[:,0]*W               , -X2[:,0]*log(2-X2[:,1])*W2])
    return ((X0.reshape(-1,1),X1.reshape(-1,1)), Wn.reshape(-1,1))

@memoize
def SingLogRightbottom( n ):
    abl    = r_jaclog(n,0)
    X,W = tensor(gauss(n,abl), gauleg(n))
    X2,W2 = tensor(gauleg(n), gauleg(n))
    X0 = hstack([ X[:,0]*X[:,1]+1-X[:,0] , X2[:,0]*X2[:,1]+1-X2[:,0]  , 1-X[:,0]         , 1-X2[:,0] ])
    X1 = hstack([ X[:,0]                 , X2[:,0]                    , X[:,0]*X[:,1]    , X2[:,0]*X2[:,1] ])
    Wn = hstack([ X[:,0]*W               , -X2[:,0]*log(2-X2[:,1])*W2 , X[:,0]*W         , -X2[:,0]*log(1+X2[:,1])*W2 ])
    return ((X0.reshape(-1,1),X1.reshape(-1,1)), Wn.reshape(-1,1))

@memoize
def SingNone(n):
    assert n>0, 'need more than zero quadrature points'
    X,W = tensor(gauleg(n), gauleg(n+1))
    Xs = (X[:,0].reshape(-1,1), X[:,1].reshape(-1,1))
    return (Xs,W.reshape(-1,1))


def SingDiag(n_gl, n_cgl):
    assert n_gl>0 and n_cgl>0, 'need more than zero quadrature points'

    X,W = tensor(gauleg(n_gl), cgauleg(n_cgl))

    W = W * (1-X[:,1])
    X[:,0] = X[:,0]*(1-X[:,1])
    X[:,1] = X[:,1] + X[:,0]

    #F =  f(X[:,0].reshape(-1,1), X[:,1].reshape(-1,1)).reshape(-1)
    #F += f(X[:,1].reshape(-1,1), X[:,0].reshape(-1,1)).reshape(-1)
    X0 = hstack([ X[:,0], X[:,1] ])
    X1 = hstack([ X[:,1], X[:,0] ])
    Wn = hstack([ W,      W      ])
    #F *= W.reshape(-1)
    return ((X0.reshape(-1,1),X1.reshape(-1,1)), Wn.reshape(-1,1))

def SingRightbottom(n_gl, n_cgl):
    assert n_gl>0 and n_cgl>0, 'need more than zero quadrature points'

    X,W = tensor(gauleg(n_gl), cgauleg(n_cgl))

    W = W * X[:,1]
    X[:,0] = X[:,0]*X[:,1]
    # F =  f(1-X[:,0].reshape(-1,1),X[:,1].reshape(-1,1)).reshape(-1)
    # F += f(1-X[:,1].reshape(-1,1),X[:,0].reshape(-1,1)).reshape(-1)
    X0 = hstack([ 1-X[:,0], 1-X[:,1] ])
    X1 = hstack([   X[:,1],   X[:,0] ])
    Wn = hstack([ W,      W      ])
    # F *= W.reshape(-1)
    return ((X0.reshape(-1,1),X1.reshape(-1,1)), Wn.reshape(-1,1))

def SingLeftupper(n_gl, n_cgl):
    assert n_gl>0 and n_cgl>0, 'need more than zero quadrature points'
    X,W = tensor(gauleg(n_gl), cgauleg(n_cgl))

    W = W * X[:,1]
    X[:,0] = X[:,0]*X[:,1]
    #F =  f(X[:,0].reshape(-1,1),1-X[:,1].reshape(-1,1)).reshape(-1)
    #F += f(X[:,1].reshape(-1,1),1-X[:,0].reshape(-1,1)).reshape(-1)
    X0 = hstack([   X[:,0],   X[:,1] ])
    X1 = hstack([ 1-X[:,1], 1-X[:,0] ])
    Wn = hstack([ W,      W      ])
    #F *= W.reshape(-1)
    return ((X0.reshape(-1,1),X1.reshape(-1,1)), Wn.reshape(-1,1))

