"""
Simulación Monte Carlo para oro (adaptación de la idea de "Time Machine").

Pregunta que responde: ¿el resultado de una estrategia viene de una estructura real
del precio o de la suerte? Para eso:
1. Se toman los retornos diarios reales del oro.
2. Se generan N caminos de precio barajando bloques de retornos reales
   (bloques de 10 días), así se conserva la volatilidad, pero se rompe el orden real.
3. Se corre la misma estrategia en cada camino y se mira la distribución de resultados.

Si la estrategia gana solo en el histórico real y no en los caminos barajados,
su resultado depende del orden específico de esos años, no de una regla repetible.

Uso:
    python3 montecarlo.py data/xau_daily.csv
"""
import random
import sys

from backtest import COST_PER_SIDE, load_prices, metrics, pos_buy_hold, pos_cross, run

N_PATHS = 1000
BLOCK = 10
SEED = 19
TRAIN_FRAC = 0.70  # solo para mostrar; la simulación usa todo el periodo


def block_bootstrap(returns, rng):
    n = len(returns)
    out = []
    while len(out) < n:
        start = rng.randrange(0, n - BLOCK)
        out.extend(returns[start:start + BLOCK])
    return out[:n]


def to_prices(p0, rets):
    p = [p0]
    for r in rets:
        p.append(p[-1] * (1 + r))
    return p


def summarize(label, values):
    values = sorted(values)
    n = len(values)
    med = values[n // 2]
    p5 = values[int(n * 0.05)]
    p95 = values[int(n * 0.95)]
    return f"{label:34s} mediana {med*100:7.1f}% | p5 {p5*100:7.1f}% | p95 {p95*100:7.1f}%"


def main(path):
    data = load_prices(path)
    prices = [p for _, p in data]
    rets = [prices[i] / prices[i - 1] - 1 for i in range(1, len(prices))]
    n = len(prices)

    strategies = {
        "EMA 9/21": lambda p: pos_cross(p, 9, 21, "ema"),
        "Comprar y mantener": pos_buy_hold,
    }

    print(f"Caminos simulados: {N_PATHS} | bloque {BLOCK} días | costo por lado {COST_PER_SIDE*100:.4f}%")
    print(f"Histórico real: {n} días.\n")

    # resultado real
    real = {}
    for name, fn in strategies.items():
        eq, tr = run(prices, fn(prices))
        real[name] = metrics(eq, tr, n)
        print(f"REAL {name:22s} retorno {real[name]['retorno']*100:7.1f}% | MDD {real[name]['mdd']*100:6.1f}%")

    rng = random.Random(SEED)
    results = {name: {"ret": [], "mdd": [], "pos": 0} for name in strategies}
    for _ in range(N_PATHS):
        sim_rets = block_bootstrap(rets, rng)
        sim_prices = to_prices(prices[0], sim_rets)
        for name, fn in strategies.items():
            eq, tr = run(sim_prices, fn(sim_prices))
            m = metrics(eq, tr, n)
            results[name]["ret"].append(m["retorno"])
            results[name]["mdd"].append(m["mdd"])
            if m["retorno"] > 0:
                results[name]["pos"] += 1

    print("\nDistribución en caminos simulados:")
    for name in strategies:
        r = results[name]
        pct_pos = r["pos"] / N_PATHS * 100
        print(summarize(name + " (retorno)", r["ret"]))
        worst = sorted(r["mdd"])
        print(f"{'  % caminos con ganancia':34s} {pct_pos:6.1f}%")
        print(f"{'  caída máxima mediana':34s} {worst[len(worst)//2]*100:6.1f}%")

    print("\nLectura:")
    print("- Si el real está muy por encima de la mediana simulada, el resultado")
    print("  depende del orden histórico concreto, no de una regla repetible.")
    print("- Si el % de caminos con ganancia es cercano a 50-60%, la estrategia")
    print("  se comporta como una moneda con sesgo pequeño, no como ventaja clara.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/xau_daily.csv")
