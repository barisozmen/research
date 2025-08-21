"""
Evolutionary Foraging Strategy Optimization with Sexual Reproduction
===================================================================

An elegant genetic algorithm exploring the evolution of foraging strategies
in a population with sexual reproduction, mate choice, and DNA-based survival.

Author: Peter Norvig (inspired implementation)
"""

import numpy as np
import matplotlib.pyplot as plt
import random
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
from enum import Enum
import math
from collections import defaultdict


class Sex(Enum):
    MALE = "male"
    FEMALE = "female"


@dataclass
class DNA:
    """
    Sophisticated DNA encoding for foraging and mating behaviors.
    Each gene is a float between 0 and 1, with specific interpretations.
    """
    # Foraging traits (8 genes)
    risk_tolerance: float       # Willingness to explore dangerous areas
    energy_efficiency: float    # How efficiently they convert food to energy
    speed: float               # Movement speed in environment
    perception: float          # Ability to detect food sources
    memory: float              # Ability to remember good locations
    cooperation: float         # Tendency to share information
    adaptability: float        # Response to environmental changes
    persistence: float         # How long to stay in one area
    
    # Mating traits (5 genes)
    selectivity: float         # How choosy about mates
    parental_investment: float # Energy devoted to offspring
    territorial: float         # Aggression in mate competition
    courtship_effort: float    # Energy spent on courtship displays
    mate_fidelity: float       # Tendency for long-term pairing
    
    # Mate choice strategy genes (8 genes for evaluating opposite sex)
    # These determine what traits this individual finds attractive in mates
    prefers_risk_tolerance: float      # Weight given to mate's risk tolerance
    prefers_energy_efficiency: float   # Weight given to mate's energy efficiency
    prefers_speed: float              # Weight given to mate's speed
    prefers_perception: float         # Weight given to mate's perception
    prefers_cooperation: float        # Weight given to mate's cooperation
    prefers_fertility: float          # Weight given to mate's fertility
    prefers_disease_resistance: float # Weight given to mate's disease resistance
    prefers_parental_investment: float # Weight given to mate's parental investment
    
    # Survival traits (4 genes)
    disease_resistance: float  # Immune system strength
    stress_tolerance: float    # Handling of environmental pressure
    longevity: float          # Natural lifespan modifier
    fertility: float          # Reproductive success rate
    
    # Sex determination (fixed at birth)
    sex_chromosome: float      # < 0.5 = female, >= 0.5 = male
    
    def __post_init__(self):
        """Ensure all values are properly bounded."""
        for field in self.__dataclass_fields__:
            value = getattr(self, field)
            setattr(self, field, max(0.0, min(1.0, value)))
    
    @classmethod
    def random(cls) -> 'DNA':
        """Generate random DNA."""
        return cls(**{field: random.random() 
                     for field in cls.__dataclass_fields__})
    
    def mutate(self, rate: float = 0.05, strength: float = 0.1) -> 'DNA':
        """Apply Gaussian mutations to genes."""
        new_values = {}
        for field in self.__dataclass_fields__:
            value = getattr(self, field)
            if random.random() < rate:
                # Gaussian mutation with reflection at boundaries
                mutation = np.random.normal(0, strength)
                new_value = value + mutation
                # Reflect at boundaries
                if new_value < 0:
                    new_value = abs(new_value)
                elif new_value > 1:
                    new_value = 2 - new_value
                new_values[field] = max(0.0, min(1.0, new_value))
            else:
                new_values[field] = value
        return DNA(**new_values)
    
    def crossover(self, other: 'DNA') -> Tuple['DNA', 'DNA']:
        """Sophisticated crossover with segment exchange."""
        fields = list(self.__dataclass_fields__.keys())
        
        # Create two crossover points for segment exchange
        point1 = random.randint(1, len(fields) - 2)
        point2 = random.randint(point1 + 1, len(fields) - 1)
        
        child1_values = {}
        child2_values = {}
        
        for i, field in enumerate(fields):
            self_val = getattr(self, field)
            other_val = getattr(other, field)
            
            if point1 <= i < point2:
                # Exchange segment
                child1_values[field] = other_val
                child2_values[field] = self_val
            else:
                # Keep original
                child1_values[field] = self_val
                child2_values[field] = other_val
        
        return DNA(**child1_values), DNA(**child2_values)
    
    @property
    def sex(self) -> Sex:
        """Determine biological sex from chromosome."""
        return Sex.FEMALE if self.sex_chromosome < 0.5 else Sex.MALE
    
    def compatibility(self, other: 'DNA') -> float:
        """Calculate genetic compatibility for mating success."""
        # Complementary traits are beneficial
        foraging_complement = abs(self.risk_tolerance - other.risk_tolerance)
        cooperation_match = 1 - abs(self.cooperation - other.cooperation)
        survival_hybrid = (self.disease_resistance + other.disease_resistance) / 2
        
        # MHC-like diversity bonus (simplified)
        diversity_bonus = sum(abs(getattr(self, f) - getattr(other, f)) 
                            for f in ['disease_resistance', 'stress_tolerance']) / 2
        
        return (foraging_complement + cooperation_match + 
                survival_hybrid + diversity_bonus) / 4


class Individual:
    """An individual organism with DNA, state, and behaviors."""
    
    def __init__(self, dna: DNA, age: int = 0, energy: float = 1.0):
        self.dna = dna
        self.age = age
        self.energy = energy
        self.generation = 0
        self.position = np.array([random.random(), random.random()])
        self.memory_map = {}  # Remembered food locations
        self.mate = None
        self.offspring_count = 0
        self.alive = True
        
        # Derived stats from DNA (balanced for sustainable populations)
        self.max_energy = 1.3 + self.dna.longevity * 0.6
        self.base_survival_rate = 0.99 + self.dna.stress_tolerance * 0.008
        
    def forage(self, environment: 'Environment') -> float:
        """Forage for food in the environment."""
        if not self.alive:
            return 0.0
            
        # Movement based on speed and memory
        if self.memory_map and random.random() < self.dna.memory:
            # Go to remembered location
            best_location = max(self.memory_map.items(), key=lambda x: x[1])
            target = np.array(best_location[0])
        else:
            # Explore randomly, biased by risk tolerance
            if self.dna.risk_tolerance > 0.5:
                # High risk, high reward areas (edges)
                target = np.array([random.choice([0.1, 0.9]), 
                                 random.choice([0.1, 0.9])])
            else:
                # Safe central areas
                target = np.array([0.4 + random.random() * 0.2,
                                 0.4 + random.random() * 0.2])
        
        # Move towards target
        direction = target - self.position
        move_distance = self.dna.speed * 0.1
        if np.linalg.norm(direction) > 0:
            self.position += direction / np.linalg.norm(direction) * move_distance
        
        # Keep in bounds
        self.position = np.clip(self.position, 0, 1)
        
        # Forage at current location
        food_found = environment.get_food(self.position, self.dna.perception)
        
        # Update memory
        if food_found > 0.1:  # Significant food source
            self.memory_map[tuple(self.position)] = food_found
            # Forget old locations (limited memory)
            if len(self.memory_map) > int(self.dna.memory * 10 + 1):
                oldest = random.choice(list(self.memory_map.keys()))
                del self.memory_map[oldest]
        
        # Convert food to energy with efficiency
        energy_gained = food_found * self.dna.energy_efficiency
        self.energy = min(self.max_energy, self.energy + energy_gained)
        
        return energy_gained
    
    def mate_choice_attractiveness(self, other: 'Individual') -> float:
        """Calculate how attractive another individual is as a mate using evolved preferences."""
        if other.dna.sex == self.dna.sex or not other.alive:
            return 0.0
        
        # Basic genetic compatibility
        compatibility = self.dna.compatibility(other.dna)
        
        # Calculate attractiveness based on this individual's evolved mate preferences
        trait_attractiveness = 0.0
        
        # Use the mate choice strategy genes to weight different traits of the potential mate
        weighted_traits = [
            self.dna.prefers_risk_tolerance * other.dna.risk_tolerance,
            self.dna.prefers_energy_efficiency * other.dna.energy_efficiency,
            self.dna.prefers_speed * other.dna.speed,
            self.dna.prefers_perception * other.dna.perception,
            self.dna.prefers_cooperation * other.dna.cooperation,
            self.dna.prefers_fertility * other.dna.fertility,
            self.dna.prefers_disease_resistance * other.dna.disease_resistance,
            self.dna.prefers_parental_investment * other.dna.parental_investment
        ]
        
        # Normalize by the sum of preference weights to get a proper attractiveness score
        preference_sum = sum([
            self.dna.prefers_risk_tolerance, self.dna.prefers_energy_efficiency,
            self.dna.prefers_speed, self.dna.prefers_perception,
            self.dna.prefers_cooperation, self.dna.prefers_fertility,
            self.dna.prefers_disease_resistance, self.dna.prefers_parental_investment
        ])
        
        if preference_sum > 0:
            trait_attractiveness = sum(weighted_traits) / preference_sum
        else:
            # If no preferences evolved, use basic fitness
            trait_attractiveness = (other.dna.fertility + other.dna.disease_resistance) / 2
        
        # Distance penalty (prefer nearby mates)
        distance = np.linalg.norm(self.position - other.position)
        distance_factor = max(0, 1 - distance * 2)
        
        # Energy consideration (healthy mates)
        energy_factor = other.energy / other.max_energy
        
        # Sex-specific bonus considerations
        sex_specific_bonus = 0.0
        if self.dna.sex == Sex.FEMALE:
            # Females might have additional preference for territorial males (protection)
            sex_specific_bonus = other.dna.territorial * 0.1
        else:
            # Males might prefer less territorial females (less competition)
            sex_specific_bonus = (1 - other.dna.territorial) * 0.1
        
        return (compatibility * 0.25 + trait_attractiveness * 0.45 + 
                distance_factor * 0.15 + energy_factor * 0.1 + sex_specific_bonus * 0.05)
    
    def attempt_mating(self, other: 'Individual') -> List['Individual']:
        """Attempt to produce offspring with another individual."""
        if (other.dna.sex == self.dna.sex or not other.alive or 
            not self.alive or self.energy < 0.15 or other.energy < 0.15):
            return []
        
        # Higher base mating success probability
        base_success = 0.75  # Further increased base rate
        fertility_bonus = (self.dna.fertility * other.dna.fertility) * 0.2
        compatibility_bonus = self.dna.compatibility(other.dna) * 0.05
        
        success_prob = min(0.98, base_success + fertility_bonus + compatibility_bonus)
        
        if random.random() > success_prob:
            return []
        
        # Determine number of offspring (can have twins/multiple births)
        fertility_factor = (self.dna.fertility + other.dna.fertility) / 2
        parental_investment = max(self.dna.parental_investment, other.dna.parental_investment)
        
        # Higher fertility and investment can lead to multiple offspring
        if fertility_factor > 0.8 and parental_investment > 0.6:
            num_offspring = random.choices([1, 2, 3], weights=[0.4, 0.5, 0.1])[0]
        elif fertility_factor > 0.6:
            num_offspring = random.choices([1, 2], weights=[0.6, 0.4])[0]
        else:
            num_offspring = 1
        
        offspring = []
        
        # Reduced energy cost for reproduction
        base_energy_cost = 0.05 + self.dna.parental_investment * 0.08
        total_energy_cost = base_energy_cost * num_offspring * 0.8  # Economies of scale
        
        # Check if parents have enough energy for multiple offspring
        if self.energy < total_energy_cost or other.energy < total_energy_cost * 0.4:
            num_offspring = 1  # Fall back to single offspring
            total_energy_cost = base_energy_cost
        
        for _ in range(num_offspring):
            # Create offspring through crossover
            child_dna1, child_dna2 = self.dna.crossover(other.dna)
            child_dna = child_dna1.mutate()
            
            # Create child with inheritance
            child = Individual(child_dna, age=0, energy=0.9)  # Higher starting energy
            child.generation = max(self.generation, other.generation) + 1
            offspring.append(child)
        
        # Apply energy costs
        self.energy -= total_energy_cost
        other.energy -= total_energy_cost * 0.4  # Lower cost for males
        
        # Track offspring count
        self.offspring_count += num_offspring
        other.offspring_count += num_offspring
        
        return offspring
    
    def age_and_die(self, environment: 'Environment') -> bool:
        """Age the individual and determine if they die."""
        if not self.alive:
            return False
        
        self.age += 1
        
        # Base energy decay (further reduced for population sustainability)
        energy_decay = 0.015 + (1 - self.dna.energy_efficiency) * 0.008
        self.energy -= energy_decay
        
        # Age-related mortality
        age_factor = 1.0
        if self.age > 50:  # Old age effects
            age_factor = math.exp(-(self.age - 50) / (self.dna.longevity * 20 + 10))
        
        # Environmental stress
        stress_factor = 1 - environment.stress_level * (1 - self.dna.stress_tolerance)
        
        # Disease pressure
        disease_factor = 1 - environment.disease_pressure * (1 - self.dna.disease_resistance)
        
        # Energy-based survival
        energy_factor = max(0.1, self.energy / self.max_energy)
        
        # Male survival bonus to maintain breeding populations
        sex_survival_bonus = 1.0
        if self.dna.sex == Sex.MALE:
            # Males get small survival bonus to prevent breeding bottlenecks
            sex_survival_bonus = 1.02
        
        # Combined survival probability
        survival_prob = (self.base_survival_rate * age_factor * 
                        stress_factor * disease_factor * energy_factor * sex_survival_bonus)
        
        if random.random() > survival_prob or self.energy <= 0:
            self.alive = False
            return False
        
        return True


class Environment:
    """Dynamic environment with resources and challenges."""
    
    def __init__(self, size: int = 100):
        self.size = size
        self.food_map = np.random.random((size, size)) * 0.5
        self.resource_patches = self._generate_patches()
        self.stress_level = 0.1
        self.disease_pressure = 0.1
        self.season = 0
        
    def _generate_patches(self) -> List[Dict]:
        """Generate resource-rich patches in the environment."""
        patches = []
        num_patches = random.randint(3, 8)
        
        for _ in range(num_patches):
            center = (random.random(), random.random())
            richness = random.uniform(0.5, 1.0)
            radius = random.uniform(0.1, 0.3)
            patches.append({
                'center': center,
                'richness': richness,
                'radius': radius
            })
        
        return patches
    
    def get_food(self, position: np.ndarray, perception: float) -> float:
        """Get food amount at a position with given perception ability."""
        base_food = 0.4  # Baseline food availability (increased to support larger populations)
        
        # Add food from patches
        patch_food = 0.0
        for patch in self.resource_patches:
            distance = np.linalg.norm(position - np.array(patch['center']))
            if distance < patch['radius']:
                patch_contribution = (patch['richness'] * 
                                    (1 - distance / patch['radius']) *
                                    perception)
                patch_food += patch_contribution
        
        # Seasonal variation
        seasonal_modifier = 0.8 + 0.4 * math.sin(self.season * math.pi / 50)
        
        total_food = (base_food + patch_food) * seasonal_modifier
        
        # Diminish food (simple depletion model)
        if total_food > 0.2:
            for patch in self.resource_patches:
                distance = np.linalg.norm(position - np.array(patch['center']))
                if distance < patch['radius']:
                    patch['richness'] *= 0.99  # Slow depletion
        
        return min(1.0, total_food)
    
    def update(self, generation: int):
        """Update environmental conditions."""
        self.season = generation
        
        # Cyclical stress and disease pressure
        self.stress_level = 0.05 + 0.15 * abs(math.sin(generation * math.pi / 30))
        self.disease_pressure = 0.05 + 0.10 * abs(math.cos(generation * math.pi / 40))
        
        # Occasionally regenerate patches (environmental change)
        if generation % 25 == 0:
            self.resource_patches = self._generate_patches()


class EvolutionaryForagingGA:
    """Sophisticated genetic algorithm for evolving foraging strategies."""
    
    def __init__(self, 
                 population_size: int = 200,
                 max_generations: int = 100,
                 mutation_rate: float = 0.05):
        self.population_size = population_size
        self.max_generations = max_generations
        self.mutation_rate = mutation_rate
        self.environment = Environment()
        self.population = []
        self.generation = 0
        self.stats_history = []
        
        # Initialize population
        self._initialize_population()
    
    def _initialize_population(self):
        """Create initial random population with balanced sexes."""
        self.population = []
        for _ in range(self.population_size):
            dna = DNA.random()
            individual = Individual(dna)
            self.population.append(individual)
    
    def _selection_and_mating(self) -> List[Individual]:
        """Handle mate selection and reproduction."""
        offspring = []
        alive_individuals = [ind for ind in self.population if ind.alive]
        
        # Separate by sex
        males = [ind for ind in alive_individuals if ind.dna.sex == Sex.MALE]
        females = [ind for ind in alive_individuals if ind.dna.sex == Sex.FEMALE]
        
        # Mating season
        # Multiple mating rounds per generation for better reproduction
        mating_rounds = 3  # Allow multiple mating attempts
        
        for round_num in range(mating_rounds):
            for female in females:
                if female.energy < 0.1:  # Lower energy threshold
                    continue
                    
                # Female chooses mate based on attractiveness and selectivity
                if not males:
                    continue
                    
                # Calculate attractiveness of all males
                male_scores = [(male, female.mate_choice_attractiveness(male)) 
                              for male in males if male.energy > 0.1 and male.alive]
                
                if not male_scores:
                    continue
                
                # Selection probability based on attractiveness and female selectivity
                if female.dna.selectivity > 0.7:
                    # Very selective: choose best male
                    chosen_male = max(male_scores, key=lambda x: x[1])[0]
                elif female.dna.selectivity > 0.3:
                    # Moderately selective: weighted random choice
                    weights = [score for _, score in male_scores]
                    if sum(weights) > 0:
                        chosen_male = random.choices([male for male, _ in male_scores], 
                                                   weights=weights)[0]
                    else:
                        continue
                else:
                    # Low selectivity: random choice among viable males
                    chosen_male = random.choice([male for male, _ in male_scores])
                
                # Attempt mating (now returns list of offspring)
                new_offspring = female.attempt_mating(chosen_male)
                offspring.extend(new_offspring)
                
                # Break if female becomes too weak for more mating attempts
                if female.energy < 0.08:
                    break
        
        return offspring
    
    def _mortality_selection(self) -> List[Individual]:
        """Apply mortality based on DNA and environmental factors."""
        survivors = []
        
        for individual in self.population:
            if individual.age_and_die(self.environment):
                survivors.append(individual)
        
        return survivors
    
    def _environmental_pressure(self, individuals: List[Individual]) -> List[Individual]:
        """Apply additional environmental selection pressure."""
        if len(individuals) <= self.population_size:
            return individuals
        
        # Score individuals for environmental fitness
        scored = []
        for ind in individuals:
            if not ind.alive:
                continue
                
            # Fitness score based on multiple factors
            foraging_score = (ind.dna.energy_efficiency * 0.3 + 
                            ind.dna.perception * 0.2 +
                            ind.dna.speed * 0.2 +
                            ind.dna.adaptability * 0.3)
            
            survival_score = (ind.dna.disease_resistance * 0.4 +
                            ind.dna.stress_tolerance * 0.4 +
                            ind.dna.longevity * 0.2)
            
            energy_score = ind.energy / ind.max_energy
            
            reproductive_score = (ind.dna.fertility * 0.6 +
                                ind.offspring_count * 0.4)
            
            # Weighted combination
            total_fitness = (foraging_score * 0.4 + 
                           survival_score * 0.3 +
                           energy_score * 0.2 +
                           reproductive_score * 0.1)
            
            scored.append((ind, total_fitness))
        
        # Select top individuals
        scored.sort(key=lambda x: x[1], reverse=True)
        return [ind for ind, _ in scored[:self.population_size]]
    
    def _collect_statistics(self):
        """Collect and store population statistics."""
        alive = [ind for ind in self.population if ind.alive]
        if not alive:
            return
        
        stats = {
            'generation': self.generation,
            'population_size': len(alive),
            'avg_energy': np.mean([ind.energy for ind in alive]),
            'avg_age': np.mean([ind.age for ind in alive]),
            'sex_ratio': len([ind for ind in alive if ind.dna.sex == Sex.MALE]) / len(alive),
            'avg_risk_tolerance': np.mean([ind.dna.risk_tolerance for ind in alive]),
            'avg_cooperation': np.mean([ind.dna.cooperation for ind in alive]),
            'avg_selectivity': np.mean([ind.dna.selectivity for ind in alive]),
            'avg_fertility': np.mean([ind.dna.fertility for ind in alive]),
            'total_offspring': sum(ind.offspring_count for ind in alive),
            'environmental_stress': self.environment.stress_level,
            'disease_pressure': self.environment.disease_pressure
        }
        
        self.stats_history.append(stats)
    
    def evolve(self) -> List[Individual]:
        """Run the evolutionary algorithm."""
        print(f"Starting evolution with {self.population_size} individuals...")
        
        for generation in range(self.max_generations):
            self.generation = generation
            
            # Update environment
            self.environment.update(generation)
            
            # Foraging phase
            for individual in self.population:
                if individual.alive:
                    individual.forage(self.environment)
            
            # Reproduction phase
            offspring = self._selection_and_mating()
            
            # Mortality phase
            survivors = self._mortality_selection()
            
            # Natural population dynamics - no artificial immigration
            alive_count = len(survivors)
            
            # Combine survivors and offspring
            next_generation = survivors + offspring
            
            # Environmental selection pressure
            self.population = self._environmental_pressure(next_generation)
            
            # Collect statistics
            self._collect_statistics()
            
            # Progress report
            if generation % 10 == 0:
                alive_count = len([ind for ind in self.population if ind.alive])
                if alive_count > 0:
                    avg_energy = np.mean([ind.energy for ind in self.population if ind.alive])
                    print(f"Generation {generation}: {alive_count} alive, "
                          f"avg energy: {avg_energy:.3f}")
                else:
                    print(f"Generation {generation}: Population extinct!")
                    break
        
        return [ind for ind in self.population if ind.alive]
    
    def visualize_evolution(self):
        """Create elegant visualizations of the evolutionary process."""
        if not self.stats_history:
            print("No statistics to visualize.")
            return
        
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle('Evolution of Foraging Strategies with Sexual Selection', 
                     fontsize=16, fontweight='bold')
        
        generations = [s['generation'] for s in self.stats_history]
        
        # Population dynamics
        axes[0, 0].plot(generations, [s['population_size'] for s in self.stats_history], 
                       'b-', linewidth=2, label='Population Size')
        axes[0, 0].set_title('Population Dynamics')
        axes[0, 0].set_xlabel('Generation')
        axes[0, 0].set_ylabel('Population Size')
        axes[0, 0].grid(True, alpha=0.3)
        
        # Energy and fitness
        axes[0, 1].plot(generations, [s['avg_energy'] for s in self.stats_history], 
                       'g-', linewidth=2, label='Average Energy')
        axes[0, 1].set_title('Population Fitness')
        axes[0, 1].set_xlabel('Generation')
        axes[0, 1].set_ylabel('Average Energy')
        axes[0, 1].grid(True, alpha=0.3)
        
        # Sex ratio
        axes[0, 2].plot(generations, [s['sex_ratio'] for s in self.stats_history], 
                       'r-', linewidth=2, label='Male Ratio')
        axes[0, 2].axhline(y=0.5, color='k', linestyle='--', alpha=0.5, label='Expected')
        axes[0, 2].set_title('Sex Ratio Dynamics')
        axes[0, 2].set_xlabel('Generation')
        axes[0, 2].set_ylabel('Proportion Male')
        axes[0, 2].legend()
        axes[0, 2].grid(True, alpha=0.3)
        
        # Behavioral traits
        axes[1, 0].plot(generations, [s['avg_risk_tolerance'] for s in self.stats_history], 
                       'orange', linewidth=2, label='Risk Tolerance')
        axes[1, 0].plot(generations, [s['avg_cooperation'] for s in self.stats_history], 
                       'purple', linewidth=2, label='Cooperation')
        axes[1, 0].set_title('Behavioral Evolution')
        axes[1, 0].set_xlabel('Generation')
        axes[1, 0].set_ylabel('Trait Value')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        # Reproductive traits
        axes[1, 1].plot(generations, [s['avg_selectivity'] for s in self.stats_history], 
                       'cyan', linewidth=2, label='Mate Selectivity')
        axes[1, 1].plot(generations, [s['avg_fertility'] for s in self.stats_history], 
                       'magenta', linewidth=2, label='Fertility')
        axes[1, 1].set_title('Sexual Selection')
        axes[1, 1].set_xlabel('Generation')
        axes[1, 1].set_ylabel('Trait Value')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        
        # Environmental pressures
        axes[1, 2].plot(generations, [s['environmental_stress'] for s in self.stats_history], 
                       'red', linewidth=2, label='Stress Level')
        axes[1, 2].plot(generations, [s['disease_pressure'] for s in self.stats_history], 
                       'brown', linewidth=2, label='Disease Pressure')
        axes[1, 2].set_title('Environmental Challenges')
        axes[1, 2].set_xlabel('Generation')
        axes[1, 2].set_ylabel('Pressure Level')
        axes[1, 2].legend()
        axes[1, 2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def analyze_final_population(self, survivors: List[Individual]):
        """Analyze the characteristics of the final evolved population."""
        if not survivors:
            print("No survivors to analyze.")
            return
        
        print("\n" + "="*60)
        print("FINAL POPULATION ANALYSIS")
        print("="*60)
        
        # Basic statistics
        males = [ind for ind in survivors if ind.dna.sex == Sex.MALE]
        females = [ind for ind in survivors if ind.dna.sex == Sex.FEMALE]
        
        print(f"Total survivors: {len(survivors)}")
        print(f"Males: {len(males)} ({len(males)/len(survivors)*100:.1f}%)")
        print(f"Females: {len(females)} ({len(females)/len(survivors)*100:.1f}%)")
        print(f"Average age: {np.mean([ind.age for ind in survivors]):.1f}")
        print(f"Average energy: {np.mean([ind.energy for ind in survivors]):.3f}")
        print(f"Total offspring produced: {sum(ind.offspring_count for ind in survivors)}")
        
        # Trait analysis
        print("\nEvolved Trait Averages:")
        print("-" * 30)
        traits = ['risk_tolerance', 'energy_efficiency', 'speed', 'perception', 
                 'memory', 'cooperation', 'adaptability', 'persistence',
                 'selectivity', 'parental_investment', 'territorial', 'fertility', 
                 'disease_resistance', 'stress_tolerance', 'longevity']
        
        for trait in traits:
            avg_value = np.mean([getattr(ind.dna, trait) for ind in survivors])
            print(f"{trait:20}: {avg_value:.3f}")
        
        # Mate preference analysis
        print("\nEvolved Mate Preferences:")
        print("-" * 30)
        preference_traits = ['prefers_risk_tolerance', 'prefers_energy_efficiency', 
                           'prefers_speed', 'prefers_perception', 'prefers_cooperation',
                           'prefers_fertility', 'prefers_disease_resistance', 
                           'prefers_parental_investment']
        
        for trait in preference_traits:
            avg_value = np.mean([getattr(ind.dna, trait) for ind in survivors])
            print(f"{trait:25}: {avg_value:.3f}")
        
        # Sex-specific analysis
        if males and females:
            print("\nSex-Specific Differences:")
            print("-" * 30)
            for trait in ['risk_tolerance', 'selectivity', 'territorial', 
                         'parental_investment', 'fertility']:
                male_avg = np.mean([getattr(ind.dna, trait) for ind in males])
                female_avg = np.mean([getattr(ind.dna, trait) for ind in females])
                diff = male_avg - female_avg
                print(f"{trait:20}: M={male_avg:.3f}, F={female_avg:.3f}, "
                      f"Diff={diff:+.3f}")
            
            print("\nSex-Specific Mate Preferences:")
            print("-" * 40)
            key_preferences = ['prefers_fertility', 'prefers_disease_resistance', 
                              'prefers_parental_investment', 'prefers_cooperation']
            for trait in key_preferences:
                male_avg = np.mean([getattr(ind.dna, trait) for ind in males])
                female_avg = np.mean([getattr(ind.dna, trait) for ind in females])
                diff = male_avg - female_avg
                print(f"{trait:25}: M={male_avg:.3f}, F={female_avg:.3f}, "
                      f"Diff={diff:+.3f}")


def main():
    """Run the evolutionary foraging experiment."""
    print("Evolutionary Foraging Strategy Optimization")
    print("==========================================")
    print("Simulating evolution of foraging behaviors with:")
    print("• Sexual reproduction and mate choice")
    print("• DNA-based survival and mating success")
    print("• Dynamic environmental pressures")
    print("• Complex multi-trait genetic system")
    print()
    
    # Create and run the genetic algorithm
    ga = EvolutionaryForagingGA(
        population_size=80,
        max_generations=40,
        mutation_rate=0.05
    )
    
    final_population = ga.evolve()
    
    # Analysis and visualization
    ga.analyze_final_population(final_population)
    ga.visualize_evolution()
    
    print("\nEvolution complete! Check the visualizations above.")
    print("Notice how different traits co-evolve under various pressures:")
    print("• Sexual selection shapes mating preferences")
    print("• Environmental pressure drives survival traits")
    print("• Genetic compatibility influences reproductive success")


if __name__ == "__main__":
    main()
