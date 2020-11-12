
from gurobipy import *

import math

def get_warm_start(project, Gamma): #returns heuristic warm start solution for given instance
    Y = init_Y(project, Gamma)
    warm_sol = warm_start(project, Gamma, Y)
    return(warm_sol) #dict = {'M':M, 'S':S, 'y':y, 'f':f}

def init_Y(project, Gamma): #returns set of (i,j) where y[i,j]==1 for feasible solution generated with LF priority-rule heuristic
    n = project.n
    V = project.V
    N = V[1:-1]
    S = {0:0} #starts
    F = {0:0} #finishes
    R = {0:project.R} #resource availability

    theta = [project.act[i].d for i in V]
    theta_hat = [math.ceil(0.5*theta[i]) for i in V]
    d = [theta[i] for i in V] #choice of duration for heuristic solution

    #serial SGS
    for i in range(1,n+1):
        E = [j for j in V if j not in F if all(i in S for i in project.act[j].pred)] #set of eligible activities
        Pr = {i:project.act[i].LF for i in E} #priority values
        j = min(Pr, key=Pr.get) #choose activity with smallest priority value
        ES = max(F[h] for h in project.act[j].pred)
        P = sorted([t for t in set(F.values()) if t >= ES]) #possible start times
        for t in P: #checking resource feasibility
            infeas = 0
            D = sorted([tau for tau in set(F.values()) if t<=tau<float('{:.15f}'.format(t+d[j]))]) #times to check
            for tau in D:
                if any(project.act[j].r[k] > R[tau][k] for k in project.K): #if not resource feasible
                    infeas = 1
                    break
            if infeas == 0: #if t is feasible start time
                S[j] = t
                F[j] = float('{:.15f}'.format(S[j] + d[j]))
                for tau in D: #updating resource availability
                    R[tau] = [R[tau][k] - project.act[j].r[k] for k in project.K]
                if F[j] not in R:
                    R[F[j]] = [R[D[-1]][k] + project.act[j].r[k] for k in project.K]
                break
    S[n+1] = max(F[h] for h in project.act[n+1].pred)
    Y = [] #(i,j) where y[i,j]==1 in heuristic solution
    for i in N:
        Y.append((0,i))
        Y.append((i,n+1))
        for j in N:
            if S[j] > F[i] - 0.00000000001:
                Y.append((i,j))
    return(Y)

def warm_start(project, Gamma, Y): #returns full feasible solution (S,F,M) given feasible set of Y

    model = Model("{}".format(project.name))
    model.setParam("OutputFlag", False)
    model.setParam("Threads", 1)

    #data
    V = project.V #activities
    N = project.V[1:-1] #non-dummy activities
    E = project.E #edges
    n = project.n #number of non-dummy activities
    K = list(range(len(project.R))) #resource types
    R_max = project.R
    r = [R_max] + [project.act[i].r for i in N] + [R_max] #resource requirement of source and sink = R_max
    theta = [project.act[i].d for i in V]
    theta_hat = [math.ceil(0.5*project.act[i].d) for i in V]
    G = list(range(Gamma+1))
    
    #variables
    S = model.addVars([(i,g) for i in V for g in G], name = "S", vtype = GRB.CONTINUOUS, lb=0)
    y = model.addVars([(i,j) for i in V for j in V], name = "y", vtype = GRB.BINARY)
    f = model.addVars([(i,j,k) for i in V for j in V for k in K], name = "f", vtype = GRB.CONTINUOUS, lb = 0)
        
    for ij in Y:
        y[ij[0],ij[1]].start = 1
    Y_prime = []
    for i in V:
        for j in V:
            if (i,j) not in Y:
                Y_prime.append((i,j))
    for ij in Y_prime:
        y[ij[0],ij[1]].start = 0

    #objective
    model.setObjective(S[n+1,Gamma], GRB.MINIMIZE)

    #constraints
    model.addConstrs(S[ij[1],g] - S[ij[0],g] >= theta[ij[0]] for ij in Y for g in G)
    model.addConstrs(S[ij[1],g+1] - S[ij[0],g] >= theta[ij[0]] + theta_hat[ij[0]] for ij in Y for g in G[:-1])
    model.addConstr(S[0,0] == 0)
    model.addConstrs(f[i,j,k] <= R_max[k]*y[i,j] for i in V for j in V if i != n+1 if j != 0 for k in K)
    model.addConstrs(r[j][k] - 0.001 <= quicksum(f[i,j,k] for i in V if i != n+1) for j in V if j != 0 for k in K)
    model.addConstrs(quicksum(f[i,j,k] for i in V if i != n+1) <= r[j][k] + 0.001 for j in V if j != 0 for k in K) #flow into of node j in V, j!=0
    model.addConstrs(r[i][k] - 0.001 <= quicksum(f[i,j,k] for j in V if j != 0) for i in V if i != n+1 for k in K) 
    model.addConstrs(quicksum(f[i,j,k] for j in V if j != 0) <= r[i][k] + 0.001 for i in V if i != n+1 for k in K) #flow out of node i in V, i!=0

    model.optimize()

    rel_LF = []
    for i in V:
        rel_LF.append(project.T - project.act[i].LF) #calcuate relative LFs, i.e. distance to (nominal) T_max
    M = [[(model.ObjVal-rel_LF[i]) - project.act[j].ES for j in V] for i in V]
    S = [[model.getVarByName("S[{},{}]".format(i,g)).X for g in G] for i in V]
    y = [[model.getVarByName("y[{},{}]".format(i,j)).X for j in V] for i in V]
    f = [[[model.getVarByName("f[{},{},{}]".format(i,j,k)).X for k in K] for j in V] for i in V]

    return({'M':M, 'S':S, 'y':y, 'f':f})

