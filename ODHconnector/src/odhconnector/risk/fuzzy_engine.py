import yaml
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# Path to config.yaml relative to this file
import os
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.yaml')


def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)


def build_fuzzy_controller():
    """
    Costruisce e ritorna un ControlSystemSimulation basato su config.yaml.
    """
    cfg = load_config()
    # Dictionary di variabili fuzzy
    antecedents = {}
    # Membership functions
    for name, section in cfg['memberships'].items():
        uni = np.linspace(section['universe'][0], section['universe'][1], 101)
        # Consequent per 'speed'
        if name == 'speed':
            var = ctrl.Consequent(uni, name)
        else:
            var = ctrl.Antecedent(uni, name)
        for term, pts in section['functions'].items():
            var[term] = fuzz.trimf(uni, pts)
        antecedents[name] = var

    # Costruzione regole
    rules = []
    for rule in cfg.get('rules', []):
        # Parsing semplice: if -> then
        cond = None
        if_part = rule.get('if', {})
        # handle top-level AND conditions only
        for key, term in if_part.items():
            expr = antecedents[key][term]
            cond = expr if cond is None else cond & expr
        then_part = rule['then']
        for out_var, out_term in then_part.items():
            target = antecedents[out_var][out_term]
            rules.append(ctrl.Rule(cond, target))

    system = ctrl.ControlSystem(rules)
    sim = ctrl.ControlSystemSimulation(system)
    return sim


def predict_speed_factor(
    traffic_risk: float,
    weather_risk: float,
    fatigue: float,
    deadline_pressure: float,
    temperature: float
) -> float:
    """
    Placeholder fuzzy prediction: restituisce fattore velocità basato
    principalmente sul rischio traffico.

    Args:
        traffic_risk: livello di rischio traffico [0,1]
        weather_risk: livello di rischio meteo [0,1]
        fatigue: livello di fatica conducente [0,1]
        deadline_pressure: livello pressione scadenze [0,1]
        temperature: temperatura ambientale (°C)

    Returns:
        speed_factor: frazione consigliata della velocità massima [0,1]
    """
    # Semplice modello: riduci velocità proporzionalmente al rischio traffico
    sf = 1.0 - traffic_risk
    # normalizza e clip
    return float(max(0.0, min(1.0, sf)))
