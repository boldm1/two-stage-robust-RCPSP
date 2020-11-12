
from gurobipy import *

import math

from load_instance import load_instance
from warm_start import get_warm_start

def warmstart_model_trans(project, Gamma, warm_start, time_limit):

    print('\n\n\ninstance: {}; Gamma = {}\nS-Gamma model w/ warm-start\n------------------------------------------\n'.format(project.name,Gamma))

    model = Model("{}_warmstart_model_trans".format(project.name))
    model.setParam("TimeLimit", time_limit)
    model.setParam("Threads", 4)

    #data
    V = project.V #activities
    N = project.V[1:-1] #non-dummy activities
    E = project.E #edges
    n = project.n #number of non-dummy activities
    K = range(len(project.R)) #resource types
    R_max = project.R
    r = [R_max] + [project.act[i].r for i in N] + [R_max] #res. required by source and sink = R_max
    theta = [project.act[i].d for i in V]
    theta_hat = [math.ceil(0.5*project.act[i].d) for i in V]
    G = range(Gamma+1)
    
    #variables
    S = model.addVars([(i,g) for i in V for g in G], name = "S", vtype = GRB.INTEGER, lb=0)
    y = model.addVars([(i,j) for i in V for j in V], name = "y", vtype = GRB.BINARY)
    f = model.addVars([(i,j,k) for i in V for j in V for k in K], name = "f", vtype = GRB.CONTINUOUS, lb = 0)
  
    #setting warm-start
    M = [[warm_start['M'][i][j] for j in V] for i in V]
    for i in V:
        for g in G:
            S[i,g].start = warm_start['S'][i][g]
        for j in V:
            y[i,j].start = warm_start['y'][i][j]
            for k in K:
                f[i,j,k].start = warm_start['f'][i][j][k]

    #objective
    model.setObjective(S[n+1,Gamma], GRB.MINIMIZE)

    #constraints
    model.addConstrs(M[i][j]*(1-y[i,j]) + S[j,g] - S[i,g] >= theta[i] for i in V for j in V for g in G)
    model.addConstrs(M[i][j]*(1-y[i,j]) + S[j,g+1] - S[i,g] >= theta[i] + theta_hat[i] for i in V for j in V for g in G[:-1])
    model.addConstr(S[0,0] == 0)

    model.addConstrs(y[e[0],e[1]] == 1 for e in E)
    model.addConstr(y[n+1,n+1] == 1)
    model.addConstrs(f[i,j,k] <= (R_max[k]+0.0001)*y[i,j] for i in V for j in V if i != n+1 if j != 0 for k in K)
    model.addConstrs(quicksum(f[i,j,k] for i in V if i != n+1) == r[j][k] for j in V if j != 0 for k in K) #flow into node j
    model.addConstrs(quicksum(f[i,j,k] for j in V if j != 0) == r[i][k] for i in V if i != n+1 for k in K) #flow into node i
    #transitivity constraints on y
    model.addConstrs(y[i,j] + y[j,i] <= 1 for i in V for j in V if (i != n+1 and j != n+1))
    model.addConstrs(y[i,j] >= y[i,p] + y[p,j] - 1 for i in V for j in V for p in V if i != j if i != p if j != p)

    model.optimize()
    model.write("warmstart_model_trans.sol")

    sol = {'status':model.Status, 'objbound':model.ObjBound, 'objval':model.ObjVal, 'mipgap':model.MIPGap, 'runtime':model.Runtime}
    return(sol)

#project = load_instance('path_to_instance_file')
project = load_instance('/home/boldm1/OneDrive/project2/code/j30.sm/j3018_5.sm')
Gamma = 3
time_limit = 20*60
warm_start = get_warm_start(project, Gamma)
sol = warmstart_model_trans(project, Gamma, warm_start, time_limit)
