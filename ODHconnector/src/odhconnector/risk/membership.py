"""
Definizione delle Membership Functions (MF) per ogni input del motore fuzzy.
Basato su: Intelligent Speed Advisory System for Optimal Energy Efficiency... (IEEE 10459507)
"""
import numpy as np
import skfuzzy as fuzz

def create_memberships():
    # Traffic risk: valori normalizzati 0–1
    traffic = np.linspace(0, 1, 101)
    mf_traffic = {
        'low':  fuzz.trimf(traffic, [0, 0, 0.3]),
        'high': fuzz.trimf(traffic, [0.4, 1, 1]),
    }

    # Weather risk: già normalizzato 0–1 (intensità pioggia, visibilità)
    weather = np.linspace(0, 1, 101)
    mf_weather = {
        'good': fuzz.trimf(weather, [0, 0, 0.4]),
        'bad':  fuzz.trimf(weather, [0.6, 1, 1]),
    }

    # Driver fatigue: 0 = fresco, 1 = stanco
    fatigue = np.linspace(0, 1, 101)
    mf_fatigue = {
        'fresh': fuzz.trimf(fatigue, [0, 0, 0.4]),
        'tired': fuzz.trimf(fatigue, [0.6, 1, 1]),
    }

    # Deadline pressure: 0 = molto anticipo, 1 = in ritardo
    deadline = np.linspace(0, 1, 101)
    mf_deadline = {
        'low':  fuzz.trimf(deadline, [0, 0, 0.4]),
        'high': fuzz.trimf(deadline, [0.6, 1, 1]),
    }

    # Ambient temperature in °C: range -20 → +40
    temp = np.linspace(-20, 40, 121)
    mf_temp = {
        'very_cold': fuzz.trimf(temp, [-20, -20, 0]),
        'cold':      fuzz.trimf(temp, [-10, 0, 10]),
        'normal':    fuzz.trimf(temp, [5, 15, 25]),
        'hot':       fuzz.trimf(temp, [20, 30, 40]),
        'very_hot':  fuzz.trimf(temp, [35, 40, 40]),
    }

    # Speed output factor: 0 = fermo, 1 = velocità normale
    speed = np.linspace(0, 1, 101)
    mf_speed = {
        'slow':   fuzz.trimf(speed, [0, 0.3, 0.6]),
        'cruise': fuzz.trimf(speed, [0.4, 0.7, 1]),
    }

    return {
        'traffic':  (traffic, mf_traffic),
        'weather':  (weather, mf_weather),
        'fatigue':  (fatigue, mf_fatigue),
        'deadline': (deadline, mf_deadline),
        'temp':     (temp, mf_temp),
        'speed':    (speed, mf_speed),
    }

def get_membership_functions():
    """
    Restituisce le funzioni di appartenenza per ogni input e output del motore fuzzy.
    """
    memberships = create_memberships()
    return {
        'traffic':  memberships['traffic'][1],
        'weather':  memberships['weather'][1],
        'fatigue':  memberships['fatigue'][1],
        'deadline': memberships['deadline'][1],
        'temp':     memberships['temp'][1],
        'speed':    memberships['speed'][1],
    }

def get_membership_values(input_name, value):
    """
    Restituisce i valori di appartenenza per un dato input e valore.
    """
    memberships = get_membership_functions()
    if input_name in memberships:
        mf = memberships[input_name]
        return {name: mf[name][int(value * 100)] for name in mf}
    else:
        raise ValueError(f"Input '{input_name}' non trovato nelle funzioni di appartenenza.")
    
def get_membership_range(input_name):
    """
    Restituisce il range di valori per un dato input.
    """
    memberships = create_memberships()
    if input_name in memberships:
        return memberships[input_name][0]
    else:
        raise ValueError(f"Input '{input_name}' non trovato nelle funzioni di appartenenza.")
    
def get_membership_names(input_name):
    """
    Restituisce i nomi delle funzioni di appartenenza per un dato input.
    """
    memberships = create_memberships()
    if input_name in memberships:
        return list(memberships[input_name][1].keys())
    else:
        raise ValueError(f"Input '{input_name}' non trovato nelle funzioni di appartenenza.")