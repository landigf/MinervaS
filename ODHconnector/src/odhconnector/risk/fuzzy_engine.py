import yaml
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import os

# Percorso al file di configurazione YAML
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.yaml')

def load_config() -> dict:
    """
    Carica la configurazione fuzzy da config.yaml.
    """
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)


def build_fuzzy_controller() -> ctrl.ControlSystemSimulation:
    """
    Costruisce un ControlSystemSimulation basato sulla configurazione YAML.
    Gestisce dinamicamente membership e regole con AND/OR nei blocchi 'if'.
    """
    cfg = load_config()

    # 1) Creazione di antecedents e consequent
    variables: dict[str, ctrl.FuzzyVariable] = {}
    for name, spec in cfg.get('memberships', {}).items():
        universe = np.linspace(spec['universe'][0], spec['universe'][1], 101)
        # Differenzia tra antecedenti e conseguente
        if name == 'speed':
            var = ctrl.Consequent(universe, name)
        else:
            var = ctrl.Antecedent(universe, name)
        # Carica funzioni di appartenenza
        for fn_name, pts in spec.get('functions', {}).items():
            var[fn_name] = fuzz.trimf(universe, pts)
        variables[name] = var

    # 2) Funzione ricorsiva per parsare blocchi 'if' con AND/OR
    def parse_clause(block: dict) -> ctrl.Antecedent:
        expr = None
        # Prima le condizioni base (chiavi non 'and'/'or')
        for key, term in block.items():
            if key in ('and', 'or'):
                continue
            expr_term = variables[key][term]
            expr = expr_term if expr is None else expr & expr_term
        # Gestione AND
        if 'and' in block:
            and_block = block['and']
            and_list = and_block if isinstance(and_block, list) else [and_block]
            for sub in and_list:
                sub_expr = parse_clause(sub)
                expr = expr & sub_expr if expr is not None else sub_expr
        # Gestione OR
        if 'or' in block:
            or_block = block['or']
            or_list = or_block if isinstance(or_block, list) else [or_block]
            for sub in or_list:
                sub_expr = parse_clause(sub)
                expr = expr | sub_expr if expr is not None else sub_expr
        return expr

    # 3) Creazione delle regole fuzzy
    rules = []
    for rule in cfg.get('rules', []):
        cond_block = rule.get('if')
        then_block = rule.get('then')
        if not cond_block or not then_block:
            continue
        antecedent_expr = parse_clause(cond_block)
        # Assume che then_block specifichi sempre 'speed'
        speed_term = variables['speed'][then_block['speed']]
        rules.append(ctrl.Rule(antecedent_expr, speed_term))

    # 4) Costruzione del sistema e della simulazione
    system = ctrl.ControlSystem(rules)
    return ctrl.ControlSystemSimulation(system)


def predict_speed_factor(
    traffic_risk: float,
    weather_risk: float,
    fatigue: float,
    deadline_pressure: float,
    temperature: float
) -> float:
    """
    Esegue il calcolo fuzzy per la velocità consigliata.

    Args:
        traffic_risk: rischio traffico normalizzato [0-1]
        weather_risk: rischio meteo normalizzato [0-1]
        fatigue: livello fatica [0-1]
        deadline_pressure: pressione deadline [0-1]
        temperature: temperatura ambiente (°C)

    Returns:
        speed_factor [0-1]
    """
    sim = build_fuzzy_controller()
    sim.input['traffic']  = traffic_risk
    sim.input['weather']  = weather_risk
    sim.input['fatigue']  = fatigue
    sim.input['deadline'] = deadline_pressure
    sim.input['temp']     = temperature
    sim.compute()
    # Stampa il valore di 'speed' defuzzificato per debug
    print(f"sim.output: {sim.output}")
    # Ritorna il valore di 'speed' defuzzificato
    return float(sim.output['speed'])