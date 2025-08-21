import operator, math, random, functools
import numpy as np
from deap import base, gp, creator, tools, algorithms

# 1. Define primitive set (our DNA alphabet)
def safe_div(a, b):
    """Safe division that avoids division by zero"""
    if abs(b) < 1e-6:
        return 1.0  # Return 1 instead of infinity
    return a / b

def safe_exp(x):
    """Safe exponential that prevents overflow"""
    if x > 100:  # Prevent overflow
        return math.exp(100)
    elif x < -100:
        return math.exp(-100)
    return math.exp(x)

def safe_log(x):
    """Safe logarithm that handles negative/zero inputs"""
    if x <= 0:
        return 0.0
    if x > 1e100:
        return math.log(1e100)
    return math.log(abs(x))

def safe_sqrt(x):
    """Safe square root that handles negative inputs"""
    if x < 0:
        return 0.0
    return math.sqrt(abs(x))

pset = gp.PrimitiveSet("MAIN", 1)  # one argument: x
pset.addPrimitive(operator.add, 2)
pset.addPrimitive(operator.sub, 2)
pset.addPrimitive(operator.mul, 2)
pset.addPrimitive(safe_div, 2)
pset.addPrimitive(operator.neg, 1)
pset.addPrimitive(math.sin, 1)
pset.addPrimitive(math.cos, 1)
pset.addPrimitive(safe_exp, 1)
pset.addPrimitive(safe_log, 1)
pset.addPrimitive(safe_sqrt, 1)
pset.addEphemeralConstant("rand", functools.partial(random.uniform, -2, 2))  # random constants
pset.renameArguments(ARG0="x")

# 2. Define fitness and individual
creator.create("FitnessMin", base.Fitness, weights=(-1.0,))  # minimize error
creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMin)

toolbox = base.Toolbox()
toolbox.register("expr", gp.genHalfAndHalf, pset=pset, min_=1, max_=3)
toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.expr)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

# 3. Compile expression trees into callable functions
toolbox.register("compile", gp.compile, pset=pset)

# 4. Training data
X = np.linspace(-3, 3, 50)
y = X**2 + np.sin(X)  # target law

# 5. Fitness function (MSE) with error handling
def evalSymbReg(individual):
    func = toolbox.compile(expr=individual)
    sqerrors = []
    
    for i, x in enumerate(X):
        try:
            result = func(x)
            # Check for invalid results
            if math.isnan(result) or math.isinf(result):
                error = 1e6  # Large penalty for invalid results
            else:
                error = (result - y[i])**2
                # Cap extremely large errors
                if error > 1e6:
                    error = 1e6
        except (OverflowError, ZeroDivisionError, ValueError, ArithmeticError):
            # Penalty for functions that cause math errors
            error = 1e6
        
        sqerrors.append(error)
    
    return math.fsum(sqerrors) / len(X),

toolbox.register("evaluate", evalSymbReg)
toolbox.register("select", tools.selTournament, tournsize=3)
toolbox.register("mate", gp.cxOnePoint)
toolbox.register("expr_mut", gp.genFull, min_=0, max_=2)
toolbox.register("mutate", gp.mutUniform, expr=toolbox.expr_mut, pset=pset)

toolbox.decorate("mate", gp.staticLimit(key=len, max_value=17))
toolbox.decorate("mutate", gp.staticLimit(key=len, max_value=17))

# 6. Run Evolution
pop = toolbox.population(n=300)
hof = tools.HallOfFame(1)  # best formula

algorithms.eaSimple(pop, toolbox, 0.5, 0.2, 40, halloffame=hof, verbose=True)

# 7. Show Result
print("Best individual:", hof[0])
func = toolbox.compile(expr=hof[0])

# Compare with target
import matplotlib.pyplot as plt
plt.scatter(X, y, label="target data")
plt.plot(X, [func(x) for x in X], label="evolved formula", color="red")
plt.legend()
plt.show()
