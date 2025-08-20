import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple
import random

class Individual:
    """Represents a beam design with width, height, and length."""
    
    def __init__(self, width: float, height: float, length: float):
        self.width = width      # beam width (m)
        self.height = height    # beam height (m) 
        self.length = length    # beam length (m)
        self.objectives = None  # [weight, deflection]
        self.rank = None
        self.crowding_distance = 0.0
        self.dominates = set()
        self.dominated_by = 0
        
    def evaluate_objectives(self):
        """Calculate weight and deflection for the beam."""
        # Material properties (steel)
        density = 7850  # kg/m³
        E = 200e9      # Young's modulus (Pa)
        force = 10000  # Applied force (N)
        
        # Cross-sectional area and moment of inertia
        area = self.width * self.height
        I = (self.width * self.height**3) / 12
        
        # Weight (minimize)
        weight = density * area * self.length
        
        # Maximum deflection at free end (minimize)
        deflection = (force * self.length**3) / (3 * E * I)
        
        self.objectives = [weight, deflection]
        return self.objectives
    
    def dominates_other(self, other):
        """Check if this individual dominates another."""
        return (all(a <= b for a, b in zip(self.objectives, other.objectives)) and
                any(a < b for a, b in zip(self.objectives, other.objectives)))

class NSGA2:
    """NSGA-II Multi-objective Genetic Algorithm implementation."""
    
    def __init__(self, population_size=100, max_generations=100):
        self.population_size = population_size
        self.max_generations = max_generations
        
        # Beam constraints
        self.width_bounds = (0.05, 0.5)    # 5cm to 50cm
        self.height_bounds = (0.1, 1.0)    # 10cm to 1m
        self.length_bounds = (2.0, 10.0)   # 2m to 10m
        
        # GA parameters
        self.crossover_prob = 0.9
        self.mutation_prob = 0.1
        self.mutation_strength = 0.1
        
    def create_individual(self) -> Individual:
        """Create a random individual within bounds."""
        width = random.uniform(*self.width_bounds)
        height = random.uniform(*self.height_bounds)
        length = random.uniform(*self.length_bounds)
        
        individual = Individual(width, height, length)
        individual.evaluate_objectives()
        return individual
        
    def initialize_population(self) -> List[Individual]:
        """Create initial random population."""
        return [self.create_individual() for _ in range(self.population_size)]
    
    def fast_non_dominated_sort(self, population: List[Individual]) -> List[List[Individual]]:
        """Perform fast non-dominated sorting."""
        # Reset domination data
        for individual in population:
            individual.dominates = set()
            individual.dominated_by = 0
            
        # Calculate domination relationships
        for i, p in enumerate(population):
            for j, q in enumerate(population):
                if i != j:
                    if p.dominates_other(q):
                        p.dominates.add(j)
                    elif q.dominates_other(p):
                        p.dominated_by += 1
        
        # Create fronts
        fronts = [[]]
        for i, individual in enumerate(population):
            if individual.dominated_by == 0:
                individual.rank = 0
                fronts[0].append(individual)
        
        front_idx = 0
        while len(fronts[front_idx]) > 0:
            next_front = []
            for individual in fronts[front_idx]:
                for j in individual.dominates:
                    population[j].dominated_by -= 1
                    if population[j].dominated_by == 0:
                        population[j].rank = front_idx + 1
                        next_front.append(population[j])
            front_idx += 1
            fronts.append(next_front)
            
        return fronts[:-1]  # Remove empty last front
    
    def calculate_crowding_distance(self, front: List[Individual]):
        """Calculate crowding distance for individuals in a front."""
        if len(front) <= 2:
            for individual in front:
                individual.crowding_distance = float('inf')
            return
            
        # Reset distances
        for individual in front:
            individual.crowding_distance = 0.0
            
        # Calculate for each objective
        for obj_idx in range(2):  # 2 objectives
            # Sort by objective value
            front.sort(key=lambda x: x.objectives[obj_idx])
            
            # Set boundary points to infinity
            front[0].crowding_distance = float('inf')
            front[-1].crowding_distance = float('inf')
            
            # Calculate normalized distances
            obj_range = front[-1].objectives[obj_idx] - front[0].objectives[obj_idx]
            if obj_range > 0:
                for i in range(1, len(front) - 1):
                    distance = (front[i+1].objectives[obj_idx] - 
                              front[i-1].objectives[obj_idx]) / obj_range
                    front[i].crowding_distance += distance
    
    def tournament_selection(self, population: List[Individual]) -> Individual:
        """Tournament selection based on rank and crowding distance."""
        tournament_size = 2
        tournament = random.sample(population, tournament_size)
        
        # Select based on rank first, then crowding distance
        winner = min(tournament, key=lambda x: (x.rank, -x.crowding_distance))
        return winner
    
    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """Simulated Binary Crossover (SBX)."""
        eta = 20  # Distribution index
        
        def sbx_crossover(p1_val, p2_val, lower, upper):
            if random.random() > self.crossover_prob:
                return p1_val, p2_val
                
            if abs(p1_val - p2_val) < 1e-14:
                return p1_val, p2_val
            
            # Calculate beta
            if p1_val < p2_val:
                y1, y2 = p1_val, p2_val
            else:
                y1, y2 = p2_val, p1_val
                
            beta_l = 1 + 2 * (y1 - lower) / (y2 - y1)
            beta_u = 1 + 2 * (upper - y2) / (y2 - y1)
            
            alpha_l = 2 - beta_l ** -(eta + 1)
            alpha_u = 2 - beta_u ** -(eta + 1)
            
            u = random.random()
            
            if u <= 1 / alpha_l:
                beta_q = (u * alpha_l) ** (1 / (eta + 1))
            else:
                beta_q = (1 / (2 - u * alpha_l)) ** (1 / (eta + 1))
                
            if u <= 1 / alpha_u:
                beta_q2 = (u * alpha_u) ** (1 / (eta + 1))
            else:
                beta_q2 = (1 / (2 - u * alpha_u)) ** (1 / (eta + 1))
            
            c1 = 0.5 * ((y1 + y2) - beta_q * abs(y2 - y1))
            c2 = 0.5 * ((y1 + y2) + beta_q * abs(y2 - y1))
            
            c1 = max(min(c1, upper), lower)
            c2 = max(min(c2, upper), lower)
            
            if random.random() <= 0.5:
                return c1, c2
            else:
                return c2, c1
        
        # Apply crossover to each parameter
        w1, w2 = sbx_crossover(parent1.width, parent2.width, *self.width_bounds)
        h1, h2 = sbx_crossover(parent1.height, parent2.height, *self.height_bounds)
        l1, l2 = sbx_crossover(parent1.length, parent2.length, *self.length_bounds)
        
        child1 = Individual(w1, h1, l1)
        child2 = Individual(w2, h2, l2)
        
        child1.evaluate_objectives()
        child2.evaluate_objectives()
        
        return child1, child2
    
    def mutate(self, individual: Individual):
        """Polynomial mutation."""
        eta = 20  # Distribution index
        
        def polynomial_mutation(val, lower, upper):
            if random.random() > self.mutation_prob:
                return val
                
            delta_l = (val - lower) / (upper - lower)
            delta_u = (upper - val) / (upper - lower)
            
            u = random.random()
            
            if u <= 0.5:
                delta_q = (2 * u) ** (1 / (eta + 1)) - 1
                val_new = val + delta_q * (val - lower)
            else:
                delta_q = 1 - (2 * (1 - u)) ** (1 / (eta + 1))
                val_new = val + delta_q * (upper - val)
                
            return max(min(val_new, upper), lower)
        
        individual.width = polynomial_mutation(individual.width, *self.width_bounds)
        individual.height = polynomial_mutation(individual.height, *self.height_bounds)
        individual.length = polynomial_mutation(individual.length, *self.length_bounds)
        
        individual.evaluate_objectives()
    
    def environmental_selection(self, population: List[Individual]) -> List[Individual]:
        """Select next generation using NSGA-II environmental selection."""
        fronts = self.fast_non_dominated_sort(population)
        
        new_population = []
        front_idx = 0
        
        # Add complete fronts
        while (front_idx < len(fronts) and 
               len(new_population) + len(fronts[front_idx]) <= self.population_size):
            self.calculate_crowding_distance(fronts[front_idx])
            new_population.extend(fronts[front_idx])
            front_idx += 1
        
        # Add partial front if needed
        if len(new_population) < self.population_size and front_idx < len(fronts):
            self.calculate_crowding_distance(fronts[front_idx])
            remaining_front = sorted(fronts[front_idx], 
                                   key=lambda x: -x.crowding_distance)
            needed = self.population_size - len(new_population)
            new_population.extend(remaining_front[:needed])
        
        return new_population
    
    def evolve(self):
        """Run the NSGA-II algorithm."""
        # Initialize population
        population = self.initialize_population()
        
        best_fronts = []  # Store first front from each generation
        
        for generation in range(self.max_generations):
            # Create offspring
            offspring = []
            while len(offspring) < self.population_size:
                parent1 = self.tournament_selection(population)
                parent2 = self.tournament_selection(population)
                
                child1, child2 = self.crossover(parent1, parent2)
                self.mutate(child1)
                self.mutate(child2)
                
                offspring.extend([child1, child2])
            
            offspring = offspring[:self.population_size]
            
            # Combine parent and offspring populations
            combined = population + offspring
            
            # Environmental selection
            population = self.environmental_selection(combined)
            
            # Store first front for analysis
            fronts = self.fast_non_dominated_sort(population)
            if fronts:
                best_fronts.append(fronts[0].copy())
            
            if generation % 20 == 0:
                print(f"Generation {generation}: Front 0 size = {len(fronts[0])}")
        
        return population, best_fronts
    
    def plot_pareto_front(self, population: List[Individual], title="Pareto Front"):
        """Plot the Pareto front."""
        fronts = self.fast_non_dominated_sort(population)
        
        if not fronts[0]:
            print("No Pareto front found")
            return
            
        # Extract objectives for plotting
        weights = [ind.objectives[0] for ind in fronts[0]]
        deflections = [ind.objectives[1] * 1000 for ind in fronts[0]]  # Convert to mm
        
        plt.figure(figsize=(10, 6))
        plt.scatter(weights, deflections, c='red', s=50, alpha=0.7)
        plt.xlabel('Weight (kg)')
        plt.ylabel('Maximum Deflection (mm)')
        plt.title(title)
        plt.grid(True, alpha=0.3)
        
        # Add some solution details
        for i, ind in enumerate(fronts[0][:5]):  # Show first 5 solutions
            plt.annotate(f'W:{ind.width:.2f}m\nH:{ind.height:.2f}m\nL:{ind.length:.1f}m',
                        xy=(ind.objectives[0], ind.objectives[1]*1000),
                        xytext=(5, 5), textcoords='offset points',
                        fontsize=8, alpha=0.7)
        
        plt.tight_layout()
        plt.show()

# Example usage and demonstration
if __name__ == "__main__":
    print("NSGA-II for Cantilever Beam Multi-objective Optimization")
    print("=" * 60)
    print("Objectives: Minimize weight AND minimize deflection")
    print("Variables: beam width, height, and length")
    print("Constraints: Practical size limits for structural beams\n")
    
    # Create and run NSGA-II
    nsga2 = NSGA2(population_size=100, max_generations=100)
    
    print("Running NSGA-II...")
    final_population, evolution_history = nsga2.evolve()
    
    # Analyze results
    fronts = nsga2.fast_non_dominated_sort(final_population)
    print(f"\nOptimization completed!")
    print(f"Pareto front contains {len(fronts[0])} solutions")
    
    # Display some optimal solutions
    print("\nSample Pareto-optimal solutions:")
    print("-" * 70)
    print(f"{'Width(m)':<8} {'Height(m)':<9} {'Length(m)':<9} {'Weight(kg)':<10} {'Deflection(mm)'}")
    print("-" * 70)
    
    # Sort by weight for display
    sorted_front = sorted(fronts[0], key=lambda x: x.objectives[0])
    for i in range(min(10, len(sorted_front))):
        ind = sorted_front[i]
        print(f"{ind.width:<8.3f} {ind.height:<9.3f} {ind.length:<9.1f} "
              f"{ind.objectives[0]:<10.1f} {ind.objectives[1]*1000:<.2f}")
    
    # Plot final Pareto front
    nsga2.plot_pareto_front(final_population, "Final Pareto Front - Beam Design")
    
    # Show evolution of solutions
    if len(evolution_history) > 1:
        plt.figure(figsize=(12, 8))
        
        generations_to_plot = [0, len(evolution_history)//4, len(evolution_history)//2, -1]
        colors = ['blue', 'green', 'orange', 'red']
        
        for i, gen_idx in enumerate(generations_to_plot):
            front = evolution_history[gen_idx]
            weights = [ind.objectives[0] for ind in front]
            deflections = [ind.objectives[1] * 1000 for ind in front]
            
            gen_label = f'Gen {gen_idx}' if gen_idx >= 0 else f'Gen {len(evolution_history)-1}'
            plt.scatter(weights, deflections, c=colors[i], alpha=0.6, 
                       label=gen_label, s=30)
        
        plt.xlabel('Weight (kg)')
        plt.ylabel('Maximum Deflection (mm)')
        plt.title('Evolution of Pareto Front Over Generations')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()
    
    print("\nNSGA-II successfully found the trade-off between beam weight and deflection!")