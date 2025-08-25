import numpy as np
import matplotlib.pyplot as plt

# Define square wave function
def square_wave(t):
    return np.where((t % (2*np.pi)) < np.pi, 1, -1)

# Time range
t = np.linspace(0, 2*np.pi, 1000)

# Square wave true function
f_true = square_wave(t)

# Partial Fourier series approximation (only odd harmonics)
def fourier_square_wave(t, N):
    result = np.zeros_like(t)
    for k in range(1, N+1, 2):  # odd harmonics only
        result += (4/np.pi) * (1/k) * np.sin(k*t)
    return result

# Plot approximations with different number of harmonics
harmonics_list = [1, 3, 5, 15]

for N in harmonics_list:
    plt.figure(figsize=(8,4))
    plt.plot(t, f_true, 'k', label="Square wave")
    plt.plot(t, fourier_square_wave(t, N), 'r', label=f"Fourier approx (N={N})")
    plt.ylim(-1.5, 1.5)
    plt.title(f"Fourier Series Approximation with N={N} terms")
    plt.legend()
    plt.grid(True)
    plt.show()
