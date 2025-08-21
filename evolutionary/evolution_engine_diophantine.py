import random
    
from matplotlib import pyplot as plt
from toolz import pipe, partial


def dict__repr__(self):
    # for each key, value pair in self, print key: value
    def format_value(k, v):
        k_str = str(k) if len(str(k)) <= 15 else str(k)[:15] + "..."
        v_str = str(v) if len(str(v)) <= 15 else str(v)[:15] + "..."
        return f"{k_str}={v_str}"
    return self.__class__.__name__ + '(' + "; ".join([format_value(k, v) for k, v in self.items()]) + ')'

    
class Score(dict):
    __repr__ = dict__repr__
class DNA(dict):
    __repr__ = dict__repr__

class Individual:
    dna: DNA
    score: Score
    fitness: float
    def __init__(self, *args, **kwargs):
        # assert there is just one dna among args
        if not len(args) in [1, 2]:
            raise ValueError("There should be one or two arguments")
        if not isinstance(args[0], DNA):
            raise ValueError("The first argument should be a DNA")
        if len(args)==2 and not isinstance(args[1], Score):
            raise ValueError("The second argument should be a Score")
        self.dna = args[0]
        self.score = args[1] if len(args)==2 else Score(diff_least_squares=0)
        self.fitness = 0
        
    def __repr__(self):
        return f"Individual({self.dna}; {self.score}; fitness={self.fitness})"
        
class Population(list[Individual]):
    def __repr__(self):
        return f"Population(N={self.N})"
    @property
    def N(self): return len(self)
    
    # implement for brackets [ ]
    def __getitem__(self, index):
        result = super().__getitem__(index)
        # If it's a slice or multiple items, wrap in Population
        if isinstance(index, slice):
            return Population(result)
        # If it's a single item, return the Individual directly
        else:
            return result
    
    def __add__(self, other):
        return Population(super().__add__(other))
    
    def __len__(self):
        return super().__len__()
    
    def __iter__(self):
        return super().__iter__()
    
    def __contains__(self, item):
        return super().__contains__(item)


import numpy as np
def black_box_function(x):
    """
    A complicated real-valued math function of one variable x:
        f(x) = exp(-0.1x) * sin(x^2) + cos(5x)/(x^2+1) + sqrt(|x|) * log(x^2+2)
    """
    term1 = np.exp(-0.1 * x) * np.sin(x**2)
    term2 = np.cos(5*x) / (x**2 + 1)
    term3 = np.sqrt(np.abs(x)) * np.log(x**2 + 2)
    return term1 + term2 + term3

def diff_least_squares(fn1, fn2):
    return sum((fn1(x)-fn2(x))**2 for x in range(100))

def make_diophantine_function(coeffs):
    def fn(x):
        res = 0
        for i, coeff in enumerate(coeffs):
            res += coeff * x**i
        return res
    return fn

def init():
    def random_diophantine_individual():
        return Individual(
            DNA(coeffs=[random.randint(-10, 10) for _ in range(4)]),
            Score(diff_least_squares=0)
        )
    return Population([random_diophantine_individual() for _ in range(100)])

def score(population):
    for individual in population:
        individual.score = Score(diff_least_squares=diff_least_squares(
            make_diophantine_function(individual.dna['coeffs']), 
            black_box_function))
    return population

def assign_fitness(population): 
    for individual in population:
        individual.fitness = 1 / (individual.score['diff_least_squares'] + 1)
    return population

def kill(population, kill_rate): 
    sorted_population = Population(sorted(population, key=lambda x: x.fitness, reverse=True))
    return sorted_population[:int(len(population) * (1-kill_rate))]

def reproduce(sorted_population, elite_rate, birth_rate):    
    N = len(sorted_population)
    N_elite = int(N*elite_rate)
    N_other = N - N_elite
    elite_pool, other_pool = sorted_population[:N_elite], sorted_population[N_elite:]
    
    parents = elite_pool + random.sample(other_pool, int(N_other * (birth_rate - elite_rate)))
    
    N_births = int(N*birth_rate)
    
    def crossover(dna1, dna2):
        # binary random choice for each coefficient. either from dna1 or dna2
        return DNA(coeffs=[random.choice([c1, c2]) for c1, c2 in zip(dna1['coeffs'], dna2['coeffs'])])
    
    def mutate(dna): 
        mutation_rate = 0.1
        
        coeffs = dna['coeffs']
        for i in range(len(coeffs)):
            if random.random() < mutation_rate:
                coeffs[i] += random.choice([-1, 1])
        return DNA(coeffs=coeffs)
    
    def make_baby(parents):
        parent1, parent2 = random.sample(parents, 2)
        baby_dna = crossover(parent1.dna, parent2.dna)
        baby_dna = mutate(baby_dna)
        return Individual(baby_dna)

    offspring_pool = [make_baby(parents) for _ in range(N_births)]
    return sorted_population + offspring_pool


def plot_function_curves(fn1, fn2):
    x = np.linspace(-10, 10, 100)
    plt.plot(x, fn1(x), label='fn1')
    plt.plot(x, fn2(x), label='fn2')
    plt.legend()
    plt.show()

def monitor(population, i, every=20):
    if i % every != 0: return population
    
    print("-"*100)
    print(f"Population size: {len(population)}")
    
    # best score and its coefficients
    best_individual = max(population, key=lambda x: x.fitness)
    print(f"Best fitness: {best_individual.fitness}")
    print(f"Best coefficients: {best_individual.dna['coeffs']}")
    
    # worst score and its coefficients
    worst_individual = min(population, key=lambda x: x.fitness)
    print(f"Worst fitness: {worst_individual.fitness}")
    print(f"Worst coefficients: {worst_individual.dna['coeffs']}")
    
    # average score
    average_fitness = sum(individual.fitness for individual in population) / len(population)
    print(f"Average fitness: {average_fitness}")
    print()
    
    plot_function_curves(black_box_function, make_diophantine_function(best_individual.dna['coeffs']))
    
    return population

pop = init()
monitor(pop, i=0)
for i in range(200):
    pop = pipe(
        pop,
        score,
        assign_fitness,
        partial(kill, kill_rate=0.2),
        partial(reproduce, birth_rate=0.25, elite_rate=0.05),
        partial(monitor, i=i, every=20),
    )
    