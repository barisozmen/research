import random
    
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
        if not len(args) == 1:
            raise ValueError("There should be just one dna among args")
        if not isinstance(args[0], DNA):
            raise ValueError("The only argument should be a DNA")
        self.dna = args[0]
        self.score = 0
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




def init(): return Population([
    Individual(DNA(code="x**2")),
    Individual(DNA(code="np.sin(x) * np.cos(x)")),
    Individual(DNA(code="np.exp(x) / (1 + np.exp(x))")),
    Individual(DNA(code="x**3 - 2*x**2 + x - 1")),
    Individual(DNA(code="np.log(abs(x) + 1) * np.sqrt(x**2 + 1)")),
    Individual(DNA(code="x**2")),
    Individual(DNA(code="np.sin(x) * np.cos(x)")),
    Individual(DNA(code="np.exp(x) / (1 + np.exp(x))")),
    Individual(DNA(code="x**3 - 2*x**2 + x - 1")),
    Individual(DNA(code="np.log(abs(x) + 1) * np.sqrt(x**2 + 1)")),
    Individual(DNA(code="np.tan(x) + np.arctan(x)")),
    Individual(DNA(code="x * np.sin(1/x) if x != 0 else 0")),
    Individual(DNA(code="np.sinh(x) - np.cosh(x/2)")),
    Individual(DNA(code="(x**4 - 3*x**2 + 2) / (x**2 + 1)")),
    Individual(DNA(code="np.exp(-x**2) * np.cos(2*np.pi*x)")),
    Individual(DNA(code="sp.gamma(x + 1) if x > -1 else float('inf')")),
    Individual(DNA(code="sp.nextprime(abs(int(x)) + 1)")),
    Individual(DNA(code="sp.prime(min(max(int(abs(x)), 1), 1000))")),
    Individual(DNA(code="sp.isprime(abs(int(x)) + 2)")),
    Individual(DNA(code="sp.primorial(min(int(abs(x)), 10))")),
    Individual(DNA(code="x * 2 + 1 if sp.isprime(int(abs(x) * 2 + 1)) else x")),
    Individual(DNA(code="sp.factorint(max(int(abs(x)), 2))")),
    Individual(DNA(code="len(sp.primefactors(max(int(abs(x)), 2)))")),
    Individual(DNA(code="sp.totient(max(int(abs(x)), 1))")),
    Individual(DNA(code="sp.divisor_count(max(int(abs(x)), 1))")),
    Individual(DNA(code="sp.nthprime(min(max(int(abs(x)), 1), 100))"))
])

def score(population):
    return population

def assign_fitness(population): return population

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
    
    def crossover(dna1, dna2): return DNA(code=f"({dna1['code']} + {dna2['code']})/2")
    def mutate(dna): return dna
    
    def make_baby(parents):
        parent1, parent2 = random.sample(parents, 2)
        baby_dna = crossover(parent1.dna, parent2.dna)
        baby_dna = mutate(baby_dna)
        return Individual(baby_dna)

    offspring_pool = [make_baby(parents) for _ in range(N_births)]
    return sorted_population + offspring_pool

def monitor(population):
    print(f"Population size: {len(population)}")
    return population

pop = init()
monitor(pop)
for _ in range(50):
    pop = pipe(
        pop,
        score,
        assign_fitness,
        partial(kill, kill_rate=0.2),
        partial(reproduce, birth_rate=0.25, elite_rate=0.05),
        monitor,
    )
    