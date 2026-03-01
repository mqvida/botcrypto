# BotCrypto Quant Trading System (MEXC + OKX)

Aplicação profissional em **Python 3.11+** para trading algorítmico em cripto com estratégias quantitativas agressivas, gestão de risco avançada, suporte a spot/futuros e base pronta para produção.

## Arquitetura

```text
/bot
   config.py
   main.py
   strategy.py
   risk_manager.py
   exchange/
       mexc.py
       okx.py
   indicators.py
   backtest.py
   logger.py
   database.py
requirements.txt
.env.example
README.md
```

## Estratégias Implementadas

- **Scalping**: RSI + cruzamento EMA + volume spike + imbalance de livro.
- **Breakout de volatilidade**: Bollinger Bands + ATR.
- **Arbitragem MEXC/OKX**: dispara quando edge líquido (`spread - taxas`) supera 0.8% configurável.
- **Grid trading dinâmico**: bandas por quantis adaptáveis ao regime.
- **Trend following**: MACD + ADX.

As estratégias podem ser ativadas/desativadas por variáveis `.env`.

## Gestão de Risco Avançada

- Position sizing por percentual de risco.
- Stop loss dinâmico (baseado em ATR).
- Take profit escalonado (configuração por níveis).
- Trailing stop.
- Controle de drawdown máximo.
- Controle de exposição (base para extensão no executor).
- Kill switch automático por drawdown e perda diária.

## Recursos de Produção

- Credenciais em `.env` (não hardcoded).
- Controle de rate limit via `ccxt`.
- Retry automático para chamadas de exchange.
- Logging estruturado em JSON.
- Persistência em SQLite via SQLAlchemy:
  - ordens,
  - trades,
  - métricas de performance.
- Painel de terminal com:
  - saldo,
  - lucro diário,
  - ROI acumulado,
  - operações abertas.

## Instalação

1. Python 3.11+
2. Instale dependências:

```bash
pip install -r requirements.txt
```

3. Configure ambiente:

```bash
cp .env.example .env
# editar .env com suas chaves e parâmetros
```

## Execução (modo contínuo)

```bash
python -m bot.main
```

## Backtesting

Exemplo rápido:

```python
import pandas as pd
from bot.backtest import Backtester

candles = pd.read_csv("historical.csv")  # colunas: open,high,low,close,volume
bt = Backtester(initial_balance=10000)
result, equity = bt.run(candles)
print(result)
bt.plot_equity_curve(equity, "equity_curve.png")
```

Métricas calculadas:
- ROI
- Sharpe ratio
- Drawdown máximo
- Win rate
- Profit factor
- Gráfico de equity curve

## Futures e alavancagem

- Cliente configurado com `defaultType=swap` para operações de derivativos.
- Alavancagem e modo futures controlados por `.env` para governança operacional.
- Multiativos (inclusive altcoins voláteis) por `SYMBOLS`.

## Módulo de ML (opcional avançado)

O `requirements.txt` já inclui base para:
- Random Forest (`scikit-learn`)
- LSTM (`tensorflow`)

Você pode adicionar `bot/ml.py` para treinar previsão de retorno/volatilidade com dados históricos e integrar o score ao `StrategyEngine`.

## Aviso importante

Este projeto é educacional e uma base profissional para evolução. Trading de alta agressividade envolve risco elevado de perda total de capital. Faça validação rigorosa em paper/sandbox antes de operar em conta real.


## Troubleshooting rápido

- **`NameError: name 'ccxt' is not defined` em `bot/exchange/okx.py`**:
  - garanta que está com a versão mais recente do projeto (arquivo `bot/exchange/okx.py` com `import ccxt.async_support as ccxt` no topo),
  - reinstale dependências: `pip install -r requirements.txt`,
  - execute novamente: `python -m bot.main`.

- **`ModuleNotFoundError` para `pandas`, `ta` etc.**:
  - instale as dependências no mesmo ambiente Python usado para rodar o bot.
