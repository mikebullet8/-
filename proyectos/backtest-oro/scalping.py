"""Prueba estrategias de scalping en velas de 15 min (GC=F, proxy del oro).

Solo largo o plano, con el mismo costo por lado que backtest.py.
Uso:
    python3 scalping.py data/gcf_15m.csv
"""
import sys

from backtest import (COST_PER_SIDE, TRAIN_FRAC, load_prices, run, metrics,
                      pos_buy_hold, pos_cross, pos_rsi_reversion, pos_bollinger_reversion)

BARS_PER_DAY = 96  # 15 min, 24 h

STRATEGIES = {
    "Comprar y mantener": pos_buy_hold,
    "EMA 5/13": lambda p: pos_cross(p, 5, 13, "ema"),
    "EMA 9/21": lambda p: pos_cross(p, 9, 21, "ema"),
    "EMA 20/50": lambda p: pos_cross(p, 20, 50, "ema"),
    "RSI 14 reversión": pos_rsi_reversion,
    "Bollinger 20,2 reversión": pos_bollinger_reversion,
}


def line(name, m):
    return (f"{name:26s} ret {m['retorno']*100:7.2f}% | MDD {m['mdd']*100:6.2f}% | "
            f"ops {m['ops']:4d} | acierto {m['acierto']*100:5.1f}% | prom/op {m['prom_op']*100:6.3f}%")


def main(path):
    data = load_prices(path)
    dates = [d for d, _ in data]
    prices = [p for _, p in data]
    n = len(prices)
    cut = int(n * TRAIN_FRAC)
    print(f"Datos: {dates[0]} a {dates[-1]} ({n} velas de 15 min, ~{n/BARS_PER_DAY:.0f} días).")
    print(f"IS hasta {dates[cut-1]} | OOS desde {dates[cut]}. Costo por lado: {COST_PER_SIDE*100:.4f}%\n")

    print("== FUERA DE MUESTRA (30% final) ==")
    for name, fn in STRATEGIES.items():
        pos = fn(prices)
        eq, tr = run(prices[cut:], pos[cut:])
        print(line(name, metrics(eq, tr, (n - cut) / BARS_PER_DAY)))

    print("\n== TODO EL PERIODO ==")
    for name, fn in STRATEGIES.items():
        pos = fn(prices)
        eq, tr = run(prices, pos)
        print(line(name, metrics(eq, tr, n / BARS_PER_DAY)))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/gcf_15m.csv")
