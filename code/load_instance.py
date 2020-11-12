
import re
import os

def load_instance(path_to_file):
    f = open(path_to_file, 'r')
    raw_lines = f.read().splitlines()
    f.close()
    data = {'E':{}, 'd':[], 'r':[]}
    line_counter = 0
    for line in raw_lines:
        ints = list(map(int, re.findall(r'\d+', line))) #list of integers in line
        if len(ints) == 0:
            line_counter += 1
            continue
        else:
            if line_counter < 18:
                if 'jobs' in line:
                    data['n'] = int(ints[0]) #number of activities (incl. dummy act's 0, n+1)
                elif 'horizon' in line:
                    data['T'] = int(ints[0]) #UB on makespan
                elif '- renewable' in line:
                    data['n_res'] = int(ints[0])
            elif 18 <= line_counter < 18+data['n']:
                jobnr = int(ints[0])-1
                data['E'][jobnr] = [int(succ)-1 for succ in ints[3:]] #ints[3:] = successors
            elif 18+data['n']+4 <= line_counter < 18+2*data['n']+4:
                data['d'].append(int(ints[2]))
                data['r'].append([int(x) for x in ints[3:]])
            elif line_counter == 18+2*data['n']+4+3:
                data['R'] = [int(x) for x in ints]
            line_counter += 1
    activities = {}
    for j in range(data['n']):
        pred = [i for i in range(j) if j in data['E'][i]]
        act = Activity(j, pred, data['E'][j], data['d'][j], data['r'][j])
        activities[j] = act
    project_name = os.path.basename(os.path.normpath(os.path.splitext(path_to_file)[0]))
    project = Project(project_name, activities, data['R'], data['T'])
    return project
    
class Activity():
    def __init__(self, id, pred, succ, d, r):
        self.id = id
        self.pred = pred #predecessors
        self.succ = succ #successors
        self.d = d #duration
        self.r = r #resource requirement

class Project():
    def __init__(self, name, act, R, T):
        self.name = name
        self.act = act
        self.V = [i for i in act] #activities
        self.E = [(i,j) for i in self.V for j in act[i].succ] #edges
        self.n = len(act)-2 #number of non-dummy activities
        self.R = R #resource availability
        self.K = range(len(R))
        self.T = T #UB on makespan (sum of activity durations)
        self.forward_pass()
        self.backward_pass()
    
    #computes ES and EF for each activity
    def forward_pass(self):
        n = self.n
        self.act[0].ES = 0
        self.act[0].EF = 0
        for j in range(1,n+2):
            self.act[j].ES = max(self.act[i].EF for i in self.act[j].pred)
            self.act[j].EF = self.act[j].ES + self.act[j].d

    #computes LF and LS for each activity
    def backward_pass(self):
        n = self.n
        self.act[n+1].LF = self.T
        self.act[n+1].LS = self.T
        for j in range(n,-1,-1):
            self.act[j].LF = min(self.act[i].LS for i in self.act[j].succ)
            self.act[j].LS = self.act[j].LF - self.act[j].d

