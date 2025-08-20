import random

class Individual:
    pass

def evolve(
    population_size,
    generations,
    elitism,
    init,
    fitness,
    select,
    crossover,
    mutate,
    verbose=False
):
    population = init(population_size)
    
    for gen in range(generations):
        print(f"Generation {gen}: {population}")
        print()
        
        scored = sorted([(ind, fitness(ind)) for ind in population], key=lambda x: x[1], reverse=True)
        
        if verbose:
            print(f"Generation {gen}: Best fitness = {scored[0][1]}")
        
        new_population = [ind for ind, _ in scored[:elitism]]
        
        parent_pairs = select([ind for ind, _ in scored], fitness, (population_size - elitism) // 2)
        
        for parent1, parent2 in parent_pairs:
            child1, child2 = crossover(parent1, parent2)
            child1 = mutate(child1)
            child2 = mutate(child2)
            new_population.extend([child1, child2])
        
        population = new_population[:population_size]
    
    best = max(population, key=fitness)
    return best, fitness(best)

def init_binary(length):
    def init(pop_size):
        return [[random.choice([0, 10]) for _ in range(length)] for _ in range(pop_size)]
    return init

def fitness_sum(ind):
    return sum(ind)

def select_tournament(tournament_size):
    def select(pop, fitness, num_pairs):
        pairs = []
        for _ in range(num_pairs):
            def tournament():
                candidates = random.sample(pop, tournament_size)
                return max(candidates, key=fitness)
            parent1 = tournament()
            parent2 = tournament()
            pairs.append((parent1, parent2))
        return pairs
    return select

def crossover_single_point(parent1, parent2):
    point = random.randint(1, len(parent1) - 1)
    child1 = parent1[:point] + parent2[point:]
    child2 = parent2[:point] + parent1[point:]
    return child1, child2

def mutate_bitflip(ind, rate):
    return [1 - gene if random.random() < rate else gene for gene in ind]

def mutate_increment_or_decrement_factory(rate):
    def mutate(individual):
        return [gene + 1 if random.random() < rate else gene - 1 if random.random() < rate else gene for gene in individual]
    return mutate

if __name__ == "__main__":
    best, best_fitness = evolve(
        population_size=20,
        generations=20,
        elitism=10,
        init=init_binary(40),
        fitness=fitness_sum,
        select=select_tournament(3),
        crossover=crossover_single_point,
        mutate=mutate_increment_or_decrement_factory(0.2),
        verbose=True
    )
    print(f"\nBest individual: {best}")
    print(f"Best fitness: {best_fitness}")