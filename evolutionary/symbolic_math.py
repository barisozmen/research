import operator, math, random, functools
import numpy as np
from deap import base, gp, creator, tools, algorithms
from scipy import integrate, special
import sympy as sp
from collections import defaultdict

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

def safe_pow(a, b):
    """Safe power function that prevents overflow"""
    try:
        if abs(a) > 1e10 or abs(b) > 10:
            return 1.0
        if a == 0 and b < 0:
            return 1.0
        result = math.pow(abs(a), min(abs(b), 10))
        if a < 0 and int(b) % 2 == 1:
            result = -result
        return result if abs(result) < 1e10 else 1e10
    except (OverflowError, ValueError):
        return 1.0

def safe_mod(a, b):
    """Safe modular arithmetic"""
    if abs(b) < 1e-6:
        return 0.0
    return float(int(abs(a)) % max(1, int(abs(b))))

def safe_gcd(a, b):
    """Safe greatest common divisor"""
    return float(math.gcd(max(1, int(abs(a))), max(1, int(abs(b)))))

def totient(n):
    """Euler's totient function - safe version"""
    n = max(1, int(abs(n)))
    if n > 1000:  # Limit for performance
        n = n % 1000 + 1
    try:
        return float(sp.totient(n))
    except:
        return float(n)

def safe_factorial(n):
    """Safe factorial with limits"""
    n = int(abs(n))
    if n > 10:
        return float(math.factorial(10))
    return float(math.factorial(n))

def safe_gamma(x):
    """Safe gamma function"""
    try:
        if x <= 0:
            return 1.0
        if x > 10:
            return special.gamma(10)
        return special.gamma(x)
    except:
        return 1.0

def numerical_derivative(func, x, h=1e-5):
    """Numerical derivative using central difference"""
    try:
        return (func(x + h) - func(x - h)) / (2 * h)
    except:
        return 0.0

def numerical_integral(func, x, a=-1, b=1):
    """Numerical integration from a to b, normalized by interval length"""
    try:
        result, _ = integrate.quad(func, a, min(b, x + 1), limit=10)
        return result / (b - a)
    except:
        return 0.0

def safe_sin_integral(x):
    """Sine integral function"""
    try:
        if abs(x) > 10:
            return 1.0
        return special.shichi(abs(x))[0]  # Shi function
    except:
        return 0.0

def safe_bessel(x, n=0):
    """Bessel function of the first kind"""
    try:
        if abs(x) > 10:
            return 0.0
        return special.jv(n, x)
    except:
        return 0.0

pset = gp.PrimitiveSet("MAIN", 1)  # one argument: x

# Basic arithmetic
pset.addPrimitive(operator.add, 2)
pset.addPrimitive(operator.sub, 2)
pset.addPrimitive(operator.mul, 2)
pset.addPrimitive(safe_div, 2)
pset.addPrimitive(safe_pow, 2)
pset.addPrimitive(operator.neg, 1)

# Safe inverse trigonometric functions
def safe_asin(x):
    """Safe arcsine"""
    x = max(-1, min(1, x))  # Clamp to valid domain
    return math.asin(x)

def safe_acos(x):
    """Safe arccosine"""
    x = max(-1, min(1, x))  # Clamp to valid domain
    return math.acos(x)

def safe_atan(x):
    """Safe arctangent"""
    if abs(x) > 1e10:
        return math.pi/2 if x > 0 else -math.pi/2
    return math.atan(x)

# Trigonometric functions
pset.addPrimitive(math.sin, 1)
pset.addPrimitive(math.cos, 1)
pset.addPrimitive(math.tan, 1)
pset.addPrimitive(safe_asin, 1)
pset.addPrimitive(safe_acos, 1)
pset.addPrimitive(safe_atan, 1)

# Hyperbolic functions
pset.addPrimitive(math.sinh, 1)
pset.addPrimitive(math.cosh, 1)
pset.addPrimitive(math.tanh, 1)

# Exponential and logarithmic
pset.addPrimitive(safe_exp, 1)
pset.addPrimitive(safe_log, 1)
pset.addPrimitive(safe_sqrt, 1)

# Number theory functions
pset.addPrimitive(safe_mod, 2)
pset.addPrimitive(safe_gcd, 2)
pset.addPrimitive(totient, 1)
pset.addPrimitive(safe_factorial, 1)

# Special functions
pset.addPrimitive(safe_gamma, 1)
pset.addPrimitive(safe_sin_integral, 1)
pset.addPrimitive(safe_bessel, 1)

# Floor and ceiling
pset.addPrimitive(math.floor, 1)
pset.addPrimitive(math.ceil, 1)

# Constants and random values
pset.addEphemeralConstant("rand", functools.partial(random.uniform, -3, 3))
pset.addEphemeralConstant("small_int", functools.partial(random.randint, 1, 10))
pset.addTerminal(math.pi, "pi")
pset.addTerminal(math.e, "e")

pset.renameArguments(ARG0="x")

# 2. Define multi-objective fitness and individual
creator.create("FitnessMulti", base.Fitness, weights=(-8.0, -1.0, -1.0))  # minimize all objectives
creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMulti)

toolbox = base.Toolbox()
toolbox.register("expr", gp.genHalfAndHalf, pset=pset, min_=1, max_=3)
toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.expr)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

# 3. Compile expression trees into callable functions
toolbox.register("compile", gp.compile, pset=pset)

# 4. Advanced Training Data - Multiple Complex Functions
np.random.seed(42)  # For reproducibility

# Create multiple datasets with different mathematical patterns
datasets = []

# Dataset 1: Polynomial with trigonometric components
X1 = np.linspace(-2, 2, 40)
y1 = X1**3 - 2*X1**2 + np.sin(2*X1) + 0.5*np.cos(X1)
datasets.append((X1, y1, "Polynomial + Trigonometric"))

# Dataset 2: Exponential decay with oscillation
X2 = np.linspace(0, 4, 40)
y2 = np.exp(-X2/2) * np.sin(3*X2) + 0.1*X2
datasets.append((X2, y2, "Exponential Decay + Oscillation"))

# Dataset 3: Number theory pattern
X3 = np.linspace(1, 20, 40)
y3 = np.array([float(sp.totient(int(x))) / x if x > 0 else 1 for x in X3])
datasets.append((X3, y3, "Totient Function Pattern"))

# Dataset 4: Special function combination
X4 = np.linspace(-1, 1, 40)
y4 = special.gamma(X4 + 2) * np.sin(np.pi * X4) + X4**2
datasets.append((X4, y4, "Gamma + Trigonometric"))

# Dataset 5: Bessel function pattern
X5 = np.linspace(0.1, 8, 40)
y5 = special.jv(1, X5) + 0.1*np.log(X5)
datasets.append((X5, y5, "Bessel Function"))

# Dataset 6: Modular arithmetic pattern
X6 = np.linspace(1, 30, 40)
y6 = np.array([float(int(x) % 7) + np.sin(x/3) for x in X6])
datasets.append((X6, y6, "Modular + Trigonometric"))

# Dataset 7: Complex polynomial
X7 = np.linspace(-1.5, 1.5, 40)
y7 = X7**4 - 3*X7**3 + 2*X7**2 - X7 + np.exp(-X7**2)
datasets.append((X7, y7, "High-order Polynomial + Gaussian"))

# Select a random dataset for this run
current_dataset_idx = random.randint(0, len(datasets) - 1)
X, y, dataset_name = datasets[current_dataset_idx]

print(f"Training on: {dataset_name}")
print(f"Data range: X ∈ [{X.min():.2f}, {X.max():.2f}], y ∈ [{y.min():.2f}, {y.max():.2f}]")


# 5. Multi-objective fitness function with normalized objectives [0,1]
def evalSymbReg(individual):
    func = toolbox.compile(expr=individual)
    sqerrors = []
    
    # Objective 1: Accuracy (MSE) - normalized to [0,1]
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
    
    raw_mse = math.fsum(sqerrors) / len(X)
    
    # Normalize accuracy: 0 = perfect fit, 1 = worst possible
    # Use sigmoid-like function to map large MSE values to [0,1]
    max_reasonable_mse = np.var(y) * 10  # 10x the target variance as "very bad"
    accuracy_normalized = min(1.0, raw_mse / max_reasonable_mse)
    
    # Objective 2: Complexity (tree size) - normalized to [0,1]
    raw_complexity = len(individual)
    max_complexity = 20  # Our tree size limit
    complexity_normalized = min(1.0, raw_complexity / max_complexity)
    
    # Objective 3: Interpretability (number of unique operations) - normalized to [0,1]
    unique_ops = len(set(str(node) for node in individual if hasattr(node, 'name')))
    max_unique_ops = 15  # Reasonable max for interpretability
    interpretability_normalized = min(1.0, unique_ops / max_unique_ops)
    
    return accuracy_normalized, complexity_normalized, interpretability_normalized

toolbox.register("evaluate", evalSymbReg)
toolbox.register("select", tools.selNSGA2)  # Multi-objective selection
toolbox.register("mate", gp.cxOnePoint)
toolbox.register("expr_mut", gp.genFull, min_=0, max_=2)
toolbox.register("mutate", gp.mutUniform, expr=toolbox.expr_mut, pset=pset)

toolbox.decorate("mate", gp.staticLimit(key=len, max_value=20))  # Slightly larger trees allowed
toolbox.decorate("mutate", gp.staticLimit(key=len, max_value=20))

# 6. Run Multi-Objective Evolution with Statistics
stats = tools.Statistics(lambda ind: ind.fitness.values)
stats.register("avg", np.mean, axis=0)
stats.register("std", np.std, axis=0)
stats.register("min", np.min, axis=0)
stats.register("max", np.max, axis=0)

pop = toolbox.population(n=1000)  # Population for multi-objective
hof = tools.ParetoFront()  # Pareto front instead of single best

print("\nStarting multi-objective evolution...")
print("Objectives (all normalized to [0-1]):")
print("1) Accuracy: 0=perfect fit, 1=worst fit (weight: -3.0)")  
print("2) Complexity: 0=simplest, 1=most complex (weight: -1.0)")
print("3) Interpretability: 0=most interpretable, 1=least interpretable (weight: -1.0)")

final_pop, logbook = algorithms.eaSimple(
    pop, toolbox, 
    cxpb=0.7,      # Higher crossover rate for diversity
    mutpb=0.3,     # Mutation rate  
    ngen=500,      # Fewer generations for multi-objective
    stats=stats,
    halloffame=hof, 
    verbose=True
)

# 7. Analyze Multi-Objective Results
print("\n" + "="*60)
print("MULTI-OBJECTIVE EVOLUTION RESULTS")
print("="*60)
print(f"Dataset: {dataset_name}")
print(f"Final population size: {len(final_pop)}")
print(f"Pareto front size: {len(hof)}")

# Sort Pareto front by accuracy for display
pareto_sorted = sorted(hof, key=lambda ind: ind.fitness.values[0])

print(f"\nPareto-optimal formulas (sorted by accuracy):")
print("Format: Accuracy[0-1] | Complexity[0-1] | Interpretability[0-1] | Formula")
print("-" * 85)
for i, individual in enumerate(pareto_sorted[:10]):  # Show top 10
    acc, comp, interp = individual.fitness.values
    print(f"{i+1:2}. {acc:8.4f} | {comp:8.4f} | {interp:8.4f} | {str(individual)[:40]}...")

# Select best formulas based on different criteria
best_accuracy = min(hof, key=lambda ind: ind.fitness.values[0])
best_simplicity = min(hof, key=lambda ind: ind.fitness.values[1])

print(f"\nBest by different criteria:")
print(f"Most accurate: {best_accuracy} (Accuracy: {best_accuracy.fitness.values[0]:.4f})")
print(f"Simplest: {best_simplicity} (Complexity: {best_simplicity.fitness.values[1]:.4f})")

# Test best accuracy formula
print("\nTesting most accurate formula...")
best_func = toolbox.compile(expr=best_accuracy)

# Calculate detailed statistics for best accuracy formula
predictions = []
errors = []
for i, x in enumerate(X):
    try:
        pred = best_func(x)
        if not (math.isnan(pred) or math.isinf(pred)):
            predictions.append(pred)
            errors.append(abs(pred - y[i]))
        else:
            predictions.append(0)
            errors.append(abs(y[i]))
    except:
        predictions.append(0)
        errors.append(abs(y[i]))

mae = np.mean(errors)
rmse = np.sqrt(np.mean([(p - t)**2 for p, t in zip(predictions, y)]))
r2 = 1 - sum([(p - t)**2 for p, t in zip(predictions, y)]) / sum([(t - np.mean(y))**2 for t in y])

print(f"Mean Absolute Error: {mae:.6f}")
print(f"Root Mean Square Error: {rmse:.6f}")
print(f"R² Score: {r2:.6f}")

# Multi-objective visualization
import matplotlib.pyplot as plt
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

# Plot 1: Function comparison (best accuracy)
ax1.scatter(X, y, label="Target data", alpha=0.7, s=50)
ax1.plot(X, predictions, label="Most accurate formula", color="red", linewidth=2)
ax1.set_xlabel("x")
ax1.set_ylabel("f(x)")
ax1.set_title(f"Best Accuracy: {dataset_name}")
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot 2: Pareto front - Accuracy vs Complexity
if len(hof) > 1:
    accuracies = [ind.fitness.values[0] for ind in hof]
    complexities = [ind.fitness.values[1] for ind in hof]
    ax2.scatter(accuracies, complexities, alpha=0.7, s=50)
    ax2.set_xlabel("Accuracy [0-1]")
    ax2.set_ylabel("Complexity [0-1]")
    ax2.set_title("Pareto Front: Accuracy vs Complexity")
    ax2.grid(True, alpha=0.3)

# Plot 3: Evolution progress (first objective only)
generations = logbook.select("gen")
min_fitness = np.array(logbook.select("min"))
avg_fitness = np.array(logbook.select("avg"))

if len(min_fitness) > 0 and len(min_fitness[0]) >= 3:
    ax3.plot(generations, min_fitness[:, 0], label="Best Accuracy", linewidth=2)
    ax3.plot(generations, avg_fitness[:, 0], label="Avg Accuracy", linewidth=2)
    ax3.set_xlabel("Generation")
    ax3.set_ylabel("Accuracy [0-1]")
    ax3.set_title("Evolution Progress - Accuracy")
    ax3.legend()
    ax3.grid(True, alpha=0.3)

# Plot 4: Multi-objective trade-offs
if len(hof) > 1:
    complexities = [ind.fitness.values[1] for ind in hof]
    accuracies = [ind.fitness.values[0] for ind in hof]
    scatter = ax4.scatter(accuracies, complexities, 
                         c=accuracies, cmap='viridis', alpha=0.7, s=50)
    ax4.set_xlabel("Accuracy [0-1]")
    ax4.set_ylabel("Complexity [0-1]")
    ax4.set_title("Trade-offs: Accuracy vs Complexity")
    ax4.grid(True, alpha=0.3)
    plt.colorbar(scatter, ax=ax4, label='Accuracy [0-1]')

plt.tight_layout()
plt.show()

print(f"\nMulti-objective evolution completed!")
print(f"Pareto front contains {len(hof)} non-dominated solutions")
print(f"Best trade-off formula: {best_accuracy}")

# Additional objectives that could be implemented:
print(f"\n" + "="*60)
print("POTENTIAL ADDITIONAL OBJECTIVES")
print("="*60)
print("5. Robustness: How sensitive the formula is to small input changes")
print("6. Generalizability: Performance on unseen data points")
print("7. Smoothness: Continuity and differentiability of the function")
print("8. Computational efficiency: Number of operations per evaluation")
print("9. Numerical precision: Avoiding loss of precision in floating point")
print("10. Domain coverage: How well it handles edge cases and extreme values")
print("11. Symmetry/Structure: Preference for mathematically elegant patterns")
print("12. Extrapolation ability: Performance outside the training domain")
