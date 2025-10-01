# scripts/extract_bahrain_2022.py
from pathlib import Path
import argparse
import pandas as pd
import numpy as np
import fastf1

# ---------- Config ----------
OUT_DEFAULT = Path("data/interim/bahrain_2022_all_laps.csv")
CACHE_DIR = Path("fastf1_cache")  # já está no .gitignore

# ---------- Helpers ----------
def to_seconds(td):
    """Converte Timedelta/NaT para float (segundos)."""
    if pd.isna(td):
        return np.nan
    return td.total_seconds()

def compute_tyre_age_if_missing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Se 'TyreLife' não existir (ou vier cheio de NaN), calcula uma idade de pneu
    por (Year, Driver, Stint) usando contagem cumulativa de voltas.
    """
    if "TyreLife" not in df.columns or df["TyreLife"].isna().all():
        df = df.sort_values(["Driver", "Stint", "LapNumber"]).copy()
        df["TyreLife"] = (
            df.groupby(["Driver", "Stint"])["LapNumber"]
              .cumcount() + 1
        )
    return df

def enrich_with_weather(laps: pd.DataFrame, weather: pd.DataFrame) -> pd.DataFrame:
    """
    Une dados de clima por 'Time' usando merge_asof (pega o valor mais próximo anterior).
    """
    # Garantir ordenação por tempo
    laps = laps.sort_values("Time").copy()
    weather = weather.sort_values("Time").copy()
    # Alguns índices vêm como timezone-aware; alinhar tipos
    # merge_asof exige a mesma dtype e ordenado
    laps["Time"] = pd.to_timedelta(laps["Time"])
    weather["Time"] = pd.to_timedelta(weather["Time"])

    merged = pd.merge_asof(
        laps, weather[["Time", "AirTemp", "TrackTemp", "Humidity", "Pressure", "WindSpeed", "WindDirection"]],
        on="Time", direction="backward"
    )
    return merged

# ---------- Main extraction ----------
def extract_bahrain_2022(out_csv: Path, out_parquet: Path | None = None):
    fastf1.Cache.enable_cache(str(CACHE_DIR))

    year = 2022
    event_name = "Bahrain Grand Prix"
    session = fastf1.get_session(year, event_name, "R")  # Race
    session.load()  # baixa dados (usa cache depois da 1ª vez)

    # Laps completos (incluindo in/out laps)
    laps = session.laps.reset_index(drop=True)

    # Mantemos tudo (dataset "todas as voltas"); criaremos flags para in/out/pit
    keep_cols = [
        "Time",             # tempo absoluto dentro da sessão (para merge com clima)
        "Driver", "DriverNumber", "Team",
        "LapNumber", "LapStartTime", "LapTime",
        "Sector1Time", "Sector2Time", "Sector3Time",
        "SpeedI1", "SpeedI2", "SpeedFL", "SpeedST",
        "Stint", "Compound", "TyreLife",
        "PitInTime", "PitOutTime", "TrackStatus",
        "Position", "IsAccurate", "Deleted",
    ]
    # Alguns campos podem faltar em versões diferentes – filtrar os que existem
    keep_cols = [c for c in keep_cols if c in laps.columns]
    df = laps[keep_cols].copy()

    # Marcações úteis
    df["IsPitInLap"] = df["PitInTime"].notna().astype(int) if "PitInTime" in df.columns else 0
    df["IsPitOutLap"] = df["PitOutTime"].notna().astype(int) if "PitOutTime" in df.columns else 0
    df["IsInOrOutLap"] = ((df.get("PitInTime").notna()) | (df.get("PitOutTime").notna())).astype(int)

    # Pneus secos apenas? -> como é "todas as voltas", apenas marcamos composto; você filtra depois
    # df = df[df["Compound"].isin(["SOFT", "MEDIUM", "HARD"])]

    # Converte tempos para segundos (além de manter o timedelta original)
    time_cols = ["LapTime", "Sector1Time", "Sector2Time", "Sector3Time"]
    for c in time_cols:
        if c in df.columns:
            df[c + "Sec"] = df[c].apply(to_seconds)

    # Garante TyreLife
    df = compute_tyre_age_if_missing(df)

    # Adiciona metadados básicos
    df["Year"] = year
    df["EventName"] = event_name
    df["Session"] = "Race"

    # Junta clima
    # session.weather_data: colunas tipicamente ["Time","AirTemp","Humidity","Pressure","TrackTemp","WindDirection","WindSpeed"]
    weather = session.weather_data.copy()
    if weather is not None and not weather.empty and "Time" in weather.columns:
        df = enrich_with_weather(df, weather)

    # Ordena e salva
    df = df.sort_values(["Driver", "LapNumber"]).reset_index(drop=True)

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    if out_parquet:
        out_parquet.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out_parquet, index=False)

    print(f"[OK] Bahrein 2022 extraído com {len(df)} voltas. CSV -> {out_csv}")
    if out_parquet:
        print(f"[OK] Parquet -> {out_parquet}")

# ---------- CLI ----------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extrai todas as voltas do GP do Bahrein 2022 (Race)")
    parser.add_argument("--out", type=Path, default=OUT_DEFAULT, help="Caminho de saída CSV")
    parser.add_argument("--parquet", type=Path, default=None, help="(Opcional) Caminho de saída Parquet")
    args = parser.parse_args()

    extract_bahrain_2022(args.out, args.parquet)
