#Folder results_bin_chi/{system} must exist
filecsv = open(f"results_bin_chi2/{system}/a{a_max}_p{p_miss}_alpha{significance_level}_w{window_length}.csv","a+")
filetxt = open(f"results_bin_chi2/{system}/a{a_max}_p{p_miss}_alpha{significance_level}_w{window_length}.txt","a+")
filecsv.seek(0)
oldfile = filecsv.read(1) #Check if file is empty

#Add header
if not oldfile:
    filecsv.write(f"length,attack,nominal \n")
    filetxt.write(f"length, value, attack_01, attack_n, attack_ms \n")


# gurobi select environment options to avoid printing
env = gp.Env(empty=True)
env.setParam(gp.GRB.Param.OutputFlag, 0)
env.setParam(gp.GRB.Param.PoolSearchMode, 1)
env.setParam(gp.GRB.Param.PoolSolutions, 3)
env.setParam(gp.GRB.Param.OptimalityTol, 1e-9) #Ensure tolarence is smaller than the range of the results!
env.start()

# optimization problem --------------------------------------------------------
# zs is a list of binary variables, 1 (attack, miss) or 0 (no attack, hit)
# xs is a list vectors of nx elements (lenght: a_length+1), closed-loop states
#    initialized with x0, the following values are constrained by the model
#    note that it is necessary to specify lower and upper bounds for xs
#    without them gurobi thinks that the problem solution is unbounded
#    (even though it should not be necessary)
m = gp.Model(env=env)
zs = [ m.addVar(vtype=gp.GRB.BINARY, name=f"z{k}") for k in range(a_length) ]
ms = [ m.addVar(vtype=gp.GRB.INTEGER, name=f"m{k}", lb=0, ub=1000) for k in range(a_max+1)]
xs = [x0] + [ m.addMVar(nx, name=f"x{k}", lb=-1000, ub=1000) for k in range(1, a_length+1) ]

# constraints that sets first and last to zero
m.addConstr(zs[0] == 0, name="initial hit")
m.addConstr(zs[-1] == 0, name="final hit")
# Variable for counting the number of completed jobs
N = m.addVar(vtype=gp.GRB.INTEGER, name="length_a_i")

# setting objective function
# currently maximizes the final value of x squared (with weight Q)
m.setObjective(xs[-2] @ Q @ xs[-2], sense=gp.GRB.MAXIMIZE)

for k in range(a_length):
    # constraints that defines the system evolution
    # these are indicator constraints, only one of the two is active
    # if the binary variable zs[k] is 1, there is an attack (miss)
    # if the binary variable zs[k] is 0, there is no attack (hit)
    m.addConstr((zs[k] == 0) >> (xs[k+1] == Phi_hit  @ xs[k]), name=f"evolution_hit_{k}")
    m.addConstr((zs[k] == 1) >> (xs[k+1] == Phi_miss @ xs[k]), name=f"evolution_miss_{k}")

for k in range(a_length - a_max):
    # constraint that defines the maximum number of consecutive deadline misses
    # note that this goes from iteration 0 to iteration a_length-a_max
    # and for each range of a_max+1 consecutive zs constrains the sum of the binary
    # variables to be less than or equal to a_max
    m.addConstr(gp.quicksum(zs[k:k+a_max+1]) <= a_max, name=f"max_misses_{k}")

for k in range(a_length - a_min):
    # constraint that defines the minimum attack duration, at the moment it is zero
    # hence this should never be active in the current setup
    m.addConstr(gp.quicksum(zs[k:k+a_min+1]) >= a_min, name=f"min_misses_{k}")


for k in range(a_max+1):
    # we are counting here the number of k-consecutive misses
    pks = [ m.addVar(vtype=gp.GRB.BINARY, name=f"p_{k}_{i}") for i in range(a_length-k-1) ]
    #auxiliary variable as we can't do calculation inside gp.max_()
    aux = [ m.addVar(vtype=gp.GRB.INTEGER, lb=-gp.GRB.INFINITY, name=f"aux_{k}_{i}") for i in range(a_length-k-1) ]
    for i in range(a_length-k-1):
        m.addConstr(aux[i] == (1-zs[i]) + gp.quicksum(zs[i+1:i+1+k]) + (1-zs[i+1+k]) - (k+1))
        m.addConstr(pks[i] == gp.max_(aux[i],0), name=f"pattern_{k}_{i}")
        m.addConstr(ms[k] == gp.quicksum(pks), name=f"misses_{k}")
#Number of completed jobs
m.addConstr(N == gp.quicksum(ms), name="sum_misses")


# adding probabilistic constraints:
# binomialtest
# we would like the sequence to be such that it cannot be rejected that the probability of a miss is less than p_miss
exp_Y = binom.ppf(1-significance_level, window_length, p_miss)
if window_length < a_length:
    for k in range(a_length - window_length+1):
        m.addConstr(gp.quicksum(zs[k:k+window_length]) <= exp_Y, name=f"prob_miss_binomial_distribution_{k}")
else:
    m.addConstr(gp.quicksum(zs) <= exp_Y, name=f"prob_miss_binomial_distribution_{k}")

#chi-2 test
#calculate probabilities for each category
probabilities = np.zeros(a_max+1)
for k in range(a_max):
    probabilities[k] = geom.pmf(k,1-p_miss,-1)
probabilities[-1] = 1 - sum(probabilities)

#Calculate bound for chi2 test and multiply by N as we can't divide with a gurobi variable in sum
chi2_bound = chi2.ppf(1-significance_level,a_max)*N
chi2_sum = 0
exp = [m.addVar(name=f"exp{k}", lb=0, ub=1000) for k in range(a_max+1)]
for k in range(a_max+1):
    #expected
    exp[k] = probabilities[k]*N
    #observed
    obs = ms[k]
    #Remove division with N and move it to bound instead
    chi2_sum = chi2_sum + (obs-exp[k])**2/probabilities[k]
m.addConstr(chi2_sum <= chi2_bound, name="prob_geometric_chi2_test")


# solve the optimization problem
m.optimize()
nSolutions = m.SolCount
if m.Status == gp.GRB.OPTIMAL:
    for sol in range(nSolutions):
        m.setParam(gp.GRB.Param.SolutionNumber, sol)
        value = m.PoolObjVal
        #Look at nominal value one step back to compare witm.setObjective(xs[-2] @ Q @ xs[-2], sense=gp.GRB.MAXIMIZE) 
        nominal_value = np.transpose(np.linalg.matrix_power(Phi_hit,a_length-1) @ x0)  @ Q @ np.linalg.matrix_power(Phi_hit,a_length-1) @ x0
        attack_01 = [int(f"{int(z.xn)}") for z in zs]
        attack_ms = [int(f"{int(m.xn)}") for m in ms]
        attack_n = [len(x)+1 for x in "".join(map(str,attack_01)).split("0")[:-1]]
    
        if sol == 0:
            #Print and write to file
            #print(a_length, value, nominal_value, attack_01, attack_n, attack_ms, sep=', ')
            filecsv.write(f"{a_length}, {value}, {nominal_value} \n")
            filetxt.write(f"{a_length}, {value}, {attack_01}, {attack_n}, {attack_ms} \n")
    

filecsv.close()
filetxt.close()
