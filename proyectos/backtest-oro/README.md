# Backtest de estrategias de oro (XAU/USD)

Prueba estrategias clásicas sobre precios diarios del oro y reporta resultados honestos:
señal al cierre, ejecución al día siguiente, costos por operación, y separación entre
muestra de ajuste (70%) y fuera de muestra (30%).

## Uso

    python3 backtest.py data/xau_daily.csv

Requiere solo Python 3 (sin librerías externas). El CSV debe tener columnas `date,price`.

## Estrategias incluidas

- Comprar y mantener (referencia)
- Cruce de medias SMA 50/200 y EMA 9/21
- MACD 12/26/9
- RSI 14 de reversión a la media
- Bandas de Bollinger 20,2 de reversión
- Ruptura de Donchian 20/10

## Limitaciones

- Datos: 2.295 días (27-jul-2020 a 7-nov-2026), tomados de la respuesta de Alpha Vantage.
  Son todos los días del calendario, incluidos fines de semana.
- El costo por lado (0,05%) es un supuesto. Ajústalo al spread real de tu broker.
- Solo largo o plano, sin apalancamiento ni stops.
- Pocas operaciones en fuera de muestra = resultado no concluyente.

## Conclusión del primer run

Ninguna estrategia gana de forma consistente. En fuera de muestra, la EMA 9/21 tiene mejor
caída máxima y Sharpe que comprar y mantener, pero con pocas operaciones. Resultados así
no garantizan ventaja futura.

## Simulación Monte Carlo (montecarlo.py)

Corre cada estrategia en 1.000 caminos de precio generados barajando bloques de 10 días
de retornos reales. Sirve para ver si el resultado real está fuera de lo que da el azar
con la misma volatilidad. Limitación: el barajado conserva la deriva promedio del oro,
así que comprar y mantener sale casi siempre positivo en la simulación.

    python3 montecarlo.py data/xau_daily.csv
