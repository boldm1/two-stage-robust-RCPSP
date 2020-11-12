
from gurobipy import *

import math

from load_instance import load_instance

def basic_model(project, Gamma, time_limit):

    print('\n\n\ninstance: {}; Gamma = {}\nBasic model\n------------------------------------------\n'.format(project.name,Gamma))

    model = Model("{}_{}_basic_model".format(project.name, Gamma))
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
   
    #objective
    model.setObjective(S[n+1,Gamma], GRB.MINIMIZE)

    #constraints
    M = quicksum(theta[i]+theta_hat[i] for i in V) #big-M. = largest possible makespan
    model.addConstrs(M*(1-y[i,j]) + S[j,g] - S[i,g] >= theta[i] for i in V for j in V for g in G)
    model.addConstrs(M*(1-y[i,j]) + S[j,g+1] - S[i,g] >= theta[i] + theta_hat[i] for i in V for j in V for g in G[:-1])
    model.addConstr(S[0,0] == 0)

    model.addConstrs(y[e[0],e[1]] == 1 for e in E)
    model.addConstr(y[n+1,n+1] == 1)
    model.addConstrs(f[i,j,k] <= (R_max[k]+0.0001)*y[i,j] for i in V for j in V if i != n+1 if j != 0 for k in K)
    model.addConstrs(quicksum(f[i,j,k] for i in V if i != n+1) == r[j][k] for j in V if j != 0 for k in K) #flow into j
    model.addConstrs(quicksum(f[i,j,k] for j in V if j != 0) == r[i][k] for i in V if i != n+1 for k in K) #flow out of i

    model.optimize()
    model.write("basic_model.sol")

    sol = {'status':model.Status, 'objbound':model.ObjBound, 'objval':model.ObjVal, 'mipgap':model.MIPGap, 'runtime':model.Runtime}
    return(sol)

#project = load_instance('path_to_instance_file')
project = load_instance('/home/boldm1/OneDrive/project2/code/j30.sm/j3018_5.sm')
Gamma = 3
time_limit = 20*60
sol = basic_model(project, Gamma, time_limit)

