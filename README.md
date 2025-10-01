# f1-tyre-strategy-simulator

## sugestão atual da estrutura 

f1-tyre-strategy-simulator/
├─ README.md
├─ LICENSE
├─ .gitignore
├─ pyproject.toml
├─ requirements.txt               # (opcional se usar pyproject)
├─ data/
│  ├─ raw/                        # dumps crus de extração (CSV/Parquet)
│  ├─ interim/                    # dados após limpeza básica
│  └─ processed/                  # datasets prontos p/ modelagem/simulação
├─ fastf1_cache/                  # cache local do FastF1 (no .gitignore)
├─ notebooks/
│  ├─ 01_eda_bahrain.ipynb
│  └─ 02_feature_engineering.ipynb
├─ src/
│  └─ f1sim/
│     ├─ __init__.py
│     ├─ config.py                # caminhos, anos, parâmetros padrão
│     ├─ io_utils.py              # leitura/escrita CSV/Parquet, paths
│     ├─ extract/
│     │  ├─ __init__.py
│     │  └─ fastf1_bahrain.py     # extração e limpeza Bahrein
│     ├─ features/
│     │  ├─ __init__.py
│     │  └─ build_features.py     # derivação de variáveis (stint_age, gaps, etc.)
│     ├─ models/
│     │  ├─ __init__.py
│     │  ├─ baselines.py          # RegLog, KNN, etc. (class/next action)
│     │  ├─ boosting.py           # LightGBM/XGB/CatBoost
│     │  ├─ sequence.py           # LSTM/TCN/CNN1D (futuro)
│     │  └─ evaluation.py         # métricas: acc, F1, Brier, MAE/ritmo, backtest
│     ├─ simulation/
│     │  ├─ __init__.py
│     │  └─ engine.py             # motor de simulação de sequência de pits
│     └─ cli.py                   # interface de linha de comando (Typer/argparse)
├─ scripts/
│  ├─ extract_bahrain.py          # script fino chamando src.f1sim.extract
│  ├─ make_features.py
│  ├─ train_models.py
│  └─ run_simulation.py
└─ tests/
   ├─ __init__.py
   ├─ test_io_utils.py
   └─ test_engine.py
