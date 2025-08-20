**Genetic Algorithms: Where They Shine, and Where They Don’t**

Genetic Algorithms (GAs) are one of those techniques that sound so intuitive you almost forget to ask where they actually make sense. You take a population of candidate solutions, encode them as chromosomes, apply mutation and crossover, and let survival of the fittest do the optimization work. The metaphor is appealing. But metaphors don’t guarantee performance.

So: when should you reach for a GA?

### When They Fit Well

1. **Poorly Understood Search Landscapes**
   If you don’t have derivatives, convexity, or even continuity, GAs are useful. They don’t need gradients. They just need a way to score fitness. Problems with noisy, discontinuous, or deceptive landscapes are good candidates.

2. **Combinatorial Optimization**
   GAs can do surprisingly well on scheduling, routing, and packing problems where the search space is astronomically large and classical exact methods (ILP, branch-and-bound) choke. For example:

   * Timetable scheduling (schools, airlines, tournaments).
   * Routing problems with non-standard constraints.
   * Circuit layout and VLSI design.

3. **Multi-Objective Optimization**
   Real-world engineering often asks for trade-offs: minimize cost while maximizing throughput, or maximize accuracy without ballooning compute. GAs (and their cousins like NSGA-II) are good at maintaining diverse sets of Pareto-optimal solutions instead of collapsing into a single point.

4. **Evolving Structures, Not Just Parameters**
   Neural architecture search, symbolic regression, or “design discovery” problems where the structure itself is uncertain benefit from GAs. Here, mutation/crossover acts as a structured prior over possible designs.

5. **Creative / Open-Ended Search**
   GAs shine in exploratory domains like procedural content generation, evolving game strategies, or even art/music generation. The stochasticity is a feature: it gives you novel, sometimes surprising results.

### When They Don’t

1. **Smooth, Differentiable Problems**
   If you can compute a gradient, almost any gradient-based optimizer will beat a GA by orders of magnitude. GAs waste samples compared to SGD, L-BFGS, or Adam.

2. **High-Dimensional Continuous Spaces**
   GAs scale poorly when you have hundreds or thousands of variables with wide ranges. The mutation/crossover operations tend to flail around in huge spaces without useful bias.

3. **Problems With Cheap Exact Methods**
   Don’t use a GA to solve linear regression, or to sort a list. Many problems already have polynomial-time or convex optimization solutions.

### The Hacker’s Perspective

The appeal of GAs is not that they are universally best-in-class, but that they are **robust, adaptable, and easy to prototype**. If your problem looks like a black box, you can usually bolt a GA on top in a weekend and get “good enough” solutions. That’s valuable.

But be pragmatic: if your problem has structure (convexity, differentiability, sparsity), exploit it with algorithms that know what they’re doing. If not, or if you want to explore without bias, GAs remain a reliable workhorse.

In short: use GAs for messy, multi-objective, or structure-evolving problems. Don’t use them for clean math.

