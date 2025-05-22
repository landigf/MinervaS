#!/usr/bin/env python3
# fuzzy_sim.py

import numpy as np
import matplotlib.pyplot as plt

# ===== Funzioni di membership =====
def trapmf(x, a, b, c, d):
    return np.maximum(0, np.minimum((x - a) / (b - a + 1e-6),
                                    np.minimum(1, (d - x) / (d - c + 1e-6))))

def trimf(x, a, b, c):
    return np.maximum(0, np.minimum((x - a) / (b - a + 1e-6),
                                    (c - x) / (c - b + 1e-6)))

# ===== Domini delle variabili =====
x_density = np.linspace(0, 100, 200)  # veicoli/km
x_rain    = np.linspace(0, 50, 200)   # mm/h
x_risk    = np.linspace(0, 100, 200)  # score di rischio

# ===== Definizione MF per input =====
dens_low  = trapmf(x_density, 0, 0, 25, 50)
dens_med  = trimf(x_density, 25, 50, 75)
dens_high = trapmf(x_density, 50, 75, 100, 100)

rain_light = trimf(x_rain, 0, 10, 20)
rain_mod   = trimf(x_rain, 10, 25, 40)
rain_heavy = trapmf(x_rain, 30, 40, 50, 50)

# ===== Definizione MF per output =====
risk_low  = trimf(x_risk, 0, 25, 50)
risk_med  = trimf(x_risk, 25, 50, 75)
risk_high = trimf(x_risk, 50, 75, 100)

# ===== Plot MF di input =====
plt.figure(figsize=(6,4))
plt.plot(x_density, dens_low,  label='Bassa')
plt.plot(x_density, dens_med,  label='Media')
plt.plot(x_density, dens_high, label='Alta')
plt.title('MF Densità traffico')
plt.xlabel('Veicoli/km')
plt.ylabel('Membership')
plt.legend()
plt.tight_layout()
plt.show()

plt.figure(figsize=(6,4))
plt.plot(x_rain, rain_light, label='Leggera')
plt.plot(x_rain, rain_mod,   label='Moderata')
plt.plot(x_rain, rain_heavy, label='Intensa')
plt.title('MF Intensità pioggia')
plt.xlabel('mm/h')
plt.ylabel('Membership')
plt.legend()
plt.tight_layout()
plt.show()

# ===== Inferenza fuzzy e defuzzificazione =====
D, R = np.meshgrid(x_density, x_rain)
risk_surface = np.zeros_like(D)

for i in range(D.shape[0]):
    for j in range(D.shape[1]):
        mu_d_low  = trapmf(D[i,j], 0, 0, 25, 50)
        mu_d_med  = trimf(D[i,j], 25, 50, 75)
        mu_d_high = trapmf(D[i,j], 50, 75, 100, 100)
        mu_r_light = trimf(R[i,j], 0, 10, 20)
        mu_r_mod   = trimf(R[i,j], 10, 25, 40)
        mu_r_heavy = trapmf(R[i,j], 30, 40, 50, 50)

        alpha_high = min(mu_d_high, mu_r_heavy)
        alpha_med  = min(mu_d_med,  mu_r_mod)
        alpha_low  = min(mu_d_low,  mu_r_light)

        agg = np.maximum.reduce([
            alpha_low  * risk_low,
            alpha_med  * risk_med,
            alpha_high * risk_high
        ])

        # usa np.trapezoid al posto di np.trapz
        num = np.trapezoid(agg * x_risk, x_risk)
        den = np.trapezoid(agg, x_risk)
        risk_surface[i,j] = num/den if den>0 else 0

# ===== Plot superficie di inferenza =====
from mpl_toolkits.mplot3d import Axes3D  # noqa
fig = plt.figure(figsize=(8,6))
ax  = fig.add_subplot(111, projection='3d')
ax.plot_surface(D, R, risk_surface, cmap='viridis', edgecolor='none')
ax.set_xlabel('Densità')
ax.set_ylabel('Pioggia')
ax.set_zlabel('Rischio')
ax.set_title('Superficie di inferenza fuzzy')
plt.tight_layout()
plt.show()
