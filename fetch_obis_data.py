"""Prioridade 3 - Importacao de fauna marinha real via OBIS.

Consulta a API publica do OBIS (https://api.obis.org/v3) por caixa delimitadora
de cada cidade x grupo taxonomico e converte o resultado em pesos de fauna no
mesmo schema do CSV proxy usado nas Prioridades 1 e 2.

Quando o OBIS retorna poucos registros para um grupo (abaixo de OBIS_MIN_RECORDS),
usa-se a tabela de fallback AquaMaps definida para o litoral de Santa Catarina,
mantendo o pipeline executavel mesmo offline ou com cobertura local escassa.

So usa a biblioteca padrao (urllib + json + csv), sem novas dependencias.
"""

from csv import DictWriter
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import math

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "Data" / "ecological-risk"
CACHE_DIR = DATA_DIR / "obis_cache"

OBIS_ENDPOINT = "https://api.obis.org/v3/occurrence"
OBIS_REQUEST_SIZE = 0  # size=0 retorna apenas o total de registros, sem payload pesado
OBIS_MIN_RECORDS = 5  # abaixo disso, usa fallback AquaMaps para o grupo
HTTP_TIMEOUT = 30

CITIES = [
    {"name": "Florianopolis", "slug": "florianopolis", "buffer_m": 27500,
     "lat": -27.5954, "lon": -48.5480},
    {"name": "Balneario Camboriu", "slug": "balneario-camboriu", "buffer_m": 27500,
     "lat": -26.9904, "lon": -48.6345},
    {"name": "Itajai", "slug": "itajai", "buffer_m": 27500,
     "lat": -26.9081, "lon": -48.6617},
]

# group (schema do CSV) -> nome cientifico/taxon consultado no OBIS
GROUPS = [
    {"group": "zooplancton_copepodes", "scientificname": "Copepoda",
     "sensitivity_weight": 0.90},
    {"group": "invertebrados_bentonicos", "scientificname": "Bivalvia",
     "sensitivity_weight": 0.85},
    {"group": "peixes_costeiros", "scientificname": "Actinopterygii",
     "sensitivity_weight": 0.70},
    {"group": "tartarugas_marinhas", "scientificname": "Testudines",
     "sensitivity_weight": 0.82},
    {"group": "aves_marinhas", "scientificname": "Lariformes",
     "sensitivity_weight": 0.66},
]

# Fallback AquaMaps para o litoral de SC (habitat_weight por grupo).
AQUAMAPS_FALLBACK = {
    "zooplancton_copepodes": 0.75,
    "invertebrados_bentonicos": 0.72,
    "peixes_costeiros": 0.78,
    "tartarugas_marinhas": 0.60,
    "aves_marinhas": 0.62,
}

FIELDS = ["city_slug", "group", "sensitivity_weight", "habitat_weight", "notes"]


def bounding_box(city):
    """Caixa delimitadora aproximada (graus) a partir do centro e do raio."""
    radius_m = city["buffer_m"]
    dlat = radius_m / 111_320.0
    dlon = radius_m / (111_320.0 * math.cos(math.radians(city["lat"])))
    return {
        "lat_min": city["lat"] - dlat,
        "lat_max": city["lat"] + dlat,
        "lon_min": city["lon"] - dlon,
        "lon_max": city["lon"] + dlon,
    }


def obis_geometry(box):
    """Poligono WKT (retangulo) aceito pelo parametro geometry do OBIS."""
    return (
        "POLYGON(("
        f"{box['lon_min']} {box['lat_min']},"
        f"{box['lon_max']} {box['lat_min']},"
        f"{box['lon_max']} {box['lat_max']},"
        f"{box['lon_min']} {box['lat_max']},"
        f"{box['lon_min']} {box['lat_min']}"
        "))"
    )


def fetch_obis_count(city, group, box):
    """Numero de ocorrencias do grupo na caixa da cidade (com cache em disco)."""
    cache_path = CACHE_DIR / f"{city['slug']}_{group['group']}.json"
    if cache_path.exists():
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        return payload.get("total", 0), True

    query = urlencode({
        "scientificname": group["scientificname"],
        "geometry": obis_geometry(box),
        "size": OBIS_REQUEST_SIZE,
    })
    url = f"{OBIS_ENDPOINT}?{query}"
    request = Request(url, headers={"User-Agent": "light-pollution-sc/1.0"})
    with urlopen(request, timeout=HTTP_TIMEOUT) as response:
        payload = json.loads(response.read().decode("utf-8"))

    cache_path.write_text(json.dumps(payload), encoding="utf-8")
    return payload.get("total", 0), False


def occurrence_to_habitat_weight(count, all_counts):
    """Normaliza a contagem de ocorrencias para um habitat_weight em [0,1].

    Usa escala logaritmica relativa ao maior valor observado entre todos os
    grupos/cidades, evitando que um grupo muito amostrado domine o indice.
    """
    if count <= 0:
        return 0.0
    max_count = max(all_counts) if all_counts else count
    if max_count <= 0:
        return 0.0
    return min(1.0, math.log1p(count) / math.log1p(max_count))


def build_weights():
    """Consulta OBIS para todas as combinacoes e monta as linhas do CSV."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    raw = {}  # (slug, group) -> {"count", "cached", "source"}
    counts = []
    for city in CITIES:
        box = bounding_box(city)
        for group in GROUPS:
            try:
                count, cached = fetch_obis_count(city, group, box)
                source = "obis"
            except Exception as error:  # rede indisponivel, timeout, etc.
                count, cached = 0, False
                source = f"erro: {error}"
            raw[(city["slug"], group["group"])] = {
                "count": count, "cached": cached, "source": source,
            }
            if count > 0:
                counts.append(count)
            flag = "cache" if cached else "rede"
            print(f"OBIS {city['slug']:>20} / {group['group']:<24} = "
                  f"{count:>6} registros ({flag})")

    rows = []
    for city in CITIES:
        for group in GROUPS:
            entry = raw[(city["slug"], group["group"])]
            count = entry["count"]
            if count >= OBIS_MIN_RECORDS:
                habitat_weight = occurrence_to_habitat_weight(count, counts)
                notes = f"OBIS: {count} ocorrencias na caixa da cidade"
            else:
                habitat_weight = AQUAMAPS_FALLBACK[group["group"]]
                notes = (f"Fallback AquaMaps (OBIS={count} < "
                         f"{OBIS_MIN_RECORDS} registros)")
            rows.append({
                "city_slug": city["slug"],
                "group": group["group"],
                "sensitivity_weight": f"{group['sensitivity_weight']:.2f}",
                "habitat_weight": f"{habitat_weight:.2f}",
                "notes": notes,
            })
    return rows


def write_weights(rows):
    output = DATA_DIR / "obis_fauna_weights.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as file:
        writer = DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return output


def main():
    rows = build_weights()
    output = write_weights(rows)
    fallback = sum(1 for row in rows if row["notes"].startswith("Fallback"))
    print(f"\nSaved fauna weights: {output}")
    print(f"Grupos via OBIS: {len(rows) - fallback} | via fallback AquaMaps: {fallback}")


if __name__ == "__main__":
    main()
