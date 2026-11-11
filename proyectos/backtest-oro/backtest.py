"""
Backtester honesto para oro (XAU/USD, datos diarios).

Reglas:
- Señal al cierre del día t, ejecución al cierre del día t+1 (sin mirar al futuro).
- Solo largo o plano (sin venta en corto).
- Costo por cambio de posición: COST_PER_SIDE (spread + comisión + deslizamiento).
- Se reporta dentro de muestra (IS, 70% inicial) y fuera de muestra (OOS, 30% final).
  Una estrategia solo cuenta si funciona en OOS, no en la muestra con que se afinó.

Uso:
    python3 backtest.py data/xau_daily.csv
"""
import csv
import math
import sys

COST_PER_SIDE = 0.0000338  # spread Vantage ~0,27-0,28 USD (mitad por lado) / precio ~4068
TRAIN_FRAC = 0.70


def load_prices(path):
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            rows.append((r["date"], float(r["price"])))
    rows.sort(key=lambda x: x[0])  # cronológico
    return rows


# ---------- indicadores (sin pandas) ----------

def sma(x, n):
    out = [None] * len(x)
    s = 0.0
    for i, v in enumerate(x):
        s += v
        if i >= n:
            s -= x[i - n]
        if i >= n - 1:
            out[i] = s / n
    return out


def ema(x, n):
    out = [None] * len(x)
    k = 2 / (n + 1)
    prev = None
    for i, v in enumerate(x):
        prev = v if prev is None else prev + k * (v - prev)
        if i >= n - 1:
            out[i] = prev
    return out


def rsi(x, n=14):
    out = [None] * len(x)
    gains, losses = [], []
    for i in range(1, len(x)):
        d = x[i] - x[i - 1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
        if len(gains) >= n:
            ag = sum(gains[-n:]) / n
            al = sum(losses[-n:]) / n
            out[i] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    return out


def bollinger_std(x, n=20):
    m = sma(x, n)
    out = [None] * len(x)
    for i in range(n - 1, len(x)):
        w = x[i - n + 1:i + 1]
        mu = m[i]
        sd = math.sqrt(sum((v - mu) ** 2 for v in w) / n)
        out[i] = (mu, sd)
    return out


def rolling_max(x, n, end_offset=1):
    # máximo de los n cierres previos (excluye el día actual)
    out = [None] * len(x)
    for i in range(n, len(x)):
        out[i] = max(x[i - n:i])
    return out


def rolling_min(x, n):
    out = [None] * len(x)
    for i in range(n, len(x)):
        out[i] = min(x[i - n:i])
    return out


# ---------- estrategias: devuelven lista de posición deseada (0 o 1) al cierre de cada día ----------

def pos_buy_hold(p):
    return [1] * len(p)


def pos_cross(p, fast, slow, kind="sma"):
    f = sma(p, fast) if kind == "sma" else ema(p, fast)
    s = sma(p, slow) if kind == "sma" else ema(p, slow)
    return [1 if (f[i] is not None and s[i] is not None and f[i] > s[i]) else 0
            for i in range(len(p))]


def pos_macd(p, fast=12, slow=26, sig=9):
    ef, es = ema(p, fast), ema(p, slow)
    macd = [None if (ef[i] is None or es[i] is None) else ef[i] - es[i] for i in range(len(p))]
    valid = [m for m in macd if m is not None]
    sg_valid = ema(valid, sig)
    sg = [None] * len(p)
    j = 0
    for i in range(len(p)):
        if macd[i] is not None:
            sg[i] = sg_valid[j]
            j += 1
    return [1 if (macd[i] is not None and sg[i] is not None and macd[i] > sg[i]) else 0
            for i in range(len(p))]


def pos_rsi_reversion(p, n=14, buy_below=30, exit_above=50):
    r = rsi(p, n)
    pos, state = [], 0
    for i in range(len(p)):
        if r[i] is not None:
            if state == 0 and r[i] < buy_below:
                state = 1
            elif state == 1 and r[i] > exit_above:
                state = 0
        pos.append(state)
    return pos


def pos_bollinger_reversion(p, n=20, k=2.0):
    bs = bollinger_std(p, n)
    pos, state = [], 0
    for i in range(len(p)):
        if bs[i] is not None:
            mu, sd = bs[i]
            if state == 0 and p[i] < mu - k * sd:
                state = 1
            elif state == 1 and p[i] >= mu:
                state = 0
        pos.append(state)
    return pos


def pos_donchian(p, entry=20, exit_=10):
    hi = rolling_max(p, entry)
    lo = rolling_min(p, exit_)
    pos, state = [], 0
    for i in range(len(p)):
        if hi[i] is not None and lo[i] is not None:
            if state == 0 and p[i] > hi[i]:
                state = 1
            elif state == 1 and p[i] < lo[i]:
                state = 0
        pos.append(state)
    return pos


STRATEGIES = {
    "Comprar y mantener": pos_buy_hold,
    "SMA 50/200 (cruce)": lambda p: pos_cross(p, 50, 200, "sma"),
    "EMA 9/21 (cruce)": lambda p: pos_cross(p, 9, 21, "ema"),
    "MACD 12/26/9": pos_macd,
    "RSI 14 reversión (<30 compra, >50 sale)": pos_rsi_reversion,
    "Bollinger 20,2 reversión": pos_bollinger_reversion,
    "Donchian 20/10 ruptura": pos_donchian,
}


# ---------- motor de backtest ----------

def run(prices, pos):
    """Retorno diario con posición de ayer. Costo al cambiar posición."""
    equity = [1.0]
    trades = []  # retornos netos de cada operación cerrada
    entry_eq = None
    cur = 0
    for i in range(1, len(prices)):
        want = pos[i - 1]  # posición decidida al cierre de i-1, ejecutada en i
        ret = prices[i] / prices[i - 1] - 1
        eq = equity[-1]
        if want != cur:
            cost = COST_PER_SIDE
            eq *= (1 - cost)
            if cur == 1 and want == 0:
                trades.append(eq / entry_eq - 1)
            if want == 1:
                entry_eq = eq
                eq *= (1 - 0)  # costo de entrada ya aplicado arriba
            cur = want
        if cur == 1:
            eq *= (1 + ret)
        equity.append(eq)
    if cur == 1:
        trades.append(equity[-1] / entry_eq - 1)
    return equity, trades


def metrics(equity, trades, n_days):
    total = equity[-1] - 1
    years = max(n_days / 365.25, 1e-9)
    cagr = (equity[-1] ** (1 / years) - 1) if equity[-1] > 0 else -1
    peak, mdd = equity[0], 0.0
    for e in equity:
        peak = max(peak, e)
        mdd = min(mdd, e / peak - 1)
    rets = [equity[i] / equity[i - 1] - 1 for i in range(1, len(equity))]
    mu = sum(rets) / len(rets)
    sd = math.sqrt(sum((r - mu) ** 2 for r in rets) / len(rets)) if len(rets) > 1 else 0
    sharpe = (mu / sd) * math.sqrt(365) if sd > 0 else 0.0
    wins = sum(1 for t in trades if t > 0)
    win_rate = wins / len(trades) if trades else 0.0
    avg_trade = sum(trades) / len(trades) if trades else 0.0
    return {
        "retorno": total, "cagr": cagr, "mdd": mdd, "sharpe": sharpe,
        "ops": len(trades), "acierto": win_rate, "prom_op": avg_trade,
    }


def fmt(m):
    return (f"ret {m['retorno']*100:7.1f}% | CAGR {m['cagr']*100:6.1f}% | "
            f"MDD {m['mdd']*100:6.1f}% | Sharpe {m['sharpe']:5.2f} | "
            f"ops {m['ops']:4d} | acierto {m['acierto']*100:5.1f}% | "
            f"prom/op {m['prom_op']*100:6.2f}%")


def main(path):
    data = load_prices(path)
    dates = [d for d, _ in data]
    prices = [p for _, p in data]
    n = len(prices)
    cut = int(n * TRAIN_FRAC)
    print(f"Datos: {dates[0]} a {dates[-1]} ({n} días). "
          f"IS: hasta {dates[cut-1]}. OOS: desde {dates[cut]}.")
    print(f"Costo por lado: {COST_PER_SIDE*100:.2f}%\n")

    results = []
    for name, fn in STRATEGIES.items():
        pos = fn(prices)
        eq_all, tr_all = run(prices, pos)
        # OOS: reinicia el equity en el punto de corte
        p_oos = prices[cut:]
        pos_oos = pos[cut:]
        eq_oos, tr_oos = run(p_oos, pos_oos)
        m_all = metrics(eq_all, tr_all, n)
        m_oos = metrics(eq_oos, tr_oos, len(p_oos))
        results.append((name, m_all, m_oos))

    print("== FUERA DE MUESTRA (lo que importa) ==")
    for name, _, m_oos in results:
        print(f"{name:42s} {fmt(m_oos)}")
    print("\n== TODO EL PERIODO ==")
    for name, m_all, _ in results:
        print(f"{name:42s} {fmt(m_all)}")

    print("\nLectura: una estrategia solo es candidata si gana a 'Comprar y mantener'")
    print("con retorno ajustado por riesgo (Sharpe) en fuera de muestra, con muchas")
    print("operaciones y tras costos. Con pocos datos o pocas operaciones, es ruido.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/xau_daily.csv")
