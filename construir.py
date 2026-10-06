"""
Atlas Electoral Biobío: genera la página web a partir de los archivos de la carpeta datos/.

Uso:
    python construir.py

Resultado:
    index.html  (una sola página, se puede abrir con doble clic o publicar en GitHub Pages)

No necesita instalar nada: solo usa la biblioteca estándar de Python 3.

Para cambiar la página casi nunca hay que tocar este archivo:
  - datos/comunas_biobio.csv   valores por comuna (una fila por comuna, una columna por indicador)
  - datos/indicadores.csv      nombre, unidad, año, fuente y nota de cada indicador
  - datos/fuentes.csv          fuentes que se citan al pie de la página
  - CONFIGURACION (abajo)      textos generales, indicador inicial, columnas de la tabla
"""

import csv
import json
from datetime import date
from pathlib import Path

CARPETA = Path(__file__).parent
DATOS = CARPETA / "datos"
SALIDA = CARPETA / "index.html"

# ---------------------------------------------------------------------------
# CONFIGURACION: cambia estos valores para ajustar la página
# ---------------------------------------------------------------------------
CONFIGURACION = {
    "titulo": "Brújula Electoral",
    # Enlace al repositorio (aparece arriba a la derecha). Déjalo vacío para ocultarlo.
    "repositorio": "https://github.com/Leandraslzrp/brujula_biobio",
    # Indicador que se ve en el mapa al abrir la página (usa el "id" de indicadores.csv)
    "indicador_inicial": "kast_2021_2v",
    # Comuna seleccionada al abrir (código CUT)
    "comuna_inicial": 8101,
    # Ejes iniciales del gráfico de cruce de datos
    "cruce_x": "pobreza_multi",
    "cruce_y": "kast_2021_2v",
    # Columnas de la tabla "Todas las comunas"
    "columnas_tabla": [
        "poblacion", "kast_2025_2v", "kast_2021_2v", "rechazo_2022", "apruebo_2020",
        "pobreza_ingresos", "pobreza_multi", "escolaridad", "pct_indigena",
        "pct_rural", "dmcs_tasa", "dep_fcm",
    ],
    # Comunas cuyo nombre se escribe sobre el mapa
    "etiquetas_mapa": [
        "Concepción", "Los Ángeles", "Lebu", "Cañete", "Tirúa", "Alto Biobío",
        "Mulchén", "Arauco", "Yumbel", "Santa Bárbara",
    ],
    # Aviso destacado en la sección de fuentes. Déjalo vacío ("") para ocultarlo.
    "aviso": (
        "Segunda vuelta presidencial 2025: por ahora hay 20 de las 33 comunas, con los "
        "porcentajes de SERVEL (100% de mesas) tal como los publicó la prensa regional. "
        "Para completar las 13 restantes, agrega los valores en la columna kast_2025_2v "
        "de datos/comunas_biobio.csv."
    ),
}

# Columnas de comunas_biobio.csv que no son indicadores
COLUMNAS_BASE = ["cut", "nombre", "provincia", "distrito"]


def leer_csv(nombre):
    with open(DATOS / nombre, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def a_numero(texto):
    """Convierte '12,5' o '12.5' en 12.5; devuelve None si la celda está vacía."""
    texto = (texto or "").strip().replace(",", ".")
    if texto == "":
        return None
    return float(texto)


def columnas_calculadas(comuna):
    """Indicadores que se calculan a partir de otros. Agrega aquí los tuyos."""
    k25, k21 = comuna.get("kast_2025_2v"), comuna.get("kast_2021_2v")
    if k25 is not None and k21 is not None:
        comuna["dif_kast_21_25"] = round(k25 - k21, 2)


def cargar_comunas(ids_indicadores):
    comunas = []
    for fila in leer_csv("comunas_biobio.csv"):
        comuna = {
            "cut": int(fila["cut"]),
            "nombre": fila["nombre"].strip(),
            "provincia": fila["provincia"].strip(),
            "distrito": int(fila["distrito"]),
        }
        for columna, valor in fila.items():
            if columna in COLUMNAS_BASE:
                continue
            numero = a_numero(valor)
            if numero is not None:
                comuna[columna] = numero
        columnas_calculadas(comuna)
        comunas.append(comuna)

    columnas_sin_ficha = {k for c in comunas for k in c} - set(COLUMNAS_BASE) - set(ids_indicadores)
    if columnas_sin_ficha:
        print("Aviso: estas columnas no están en indicadores.csv y no se mostrarán:", sorted(columnas_sin_ficha))
    return comunas


def cargar_indicadores(fuentes):
    indicadores = []
    for fila in leer_csv("indicadores.csv"):
        if fila["fuente_id"] not in fuentes:
            raise ValueError(f"El indicador {fila['id']} usa la fuente '{fila['fuente_id']}', que no está en fuentes.csv")
        # La página usa nombres de campo cortos
        indicadores.append({
            "id": fila["id"].strip(),
            "g": fila["grupo"],
            "l": fila["nombre"],
            "s": fila["nombre_corto"],
            "u": fila["unidad"],
            "y": fila["anio"],
            "src": fila["fuente_id"],
            "n": fila["nota"],
            "int": fila["entero"].strip().lower() == "si",
        })
    return indicadores


def buscar_faltantes(comunas, indicadores):
    """Para cada indicador, lista las comunas sin dato. Se muestra como alerta arriba de la página."""
    faltantes = []
    for ind in indicadores:
        sin_dato = [c["nombre"] for c in comunas if ind["id"] not in c]
        if sin_dato:
            faltantes.append({"id": ind["id"], "nombre": ind["l"], "anio": ind["y"], "comunas": sin_dato})
    return faltantes


def cargar_fuentes():
    return {f["id"]: f for f in leer_csv("fuentes.csv")}


def cargar_geojson(nombre):
    return json.loads((DATOS / nombre).read_text(encoding="utf-8"))


def a_js(objeto):
    # "</" se escapa para que ningún texto pueda cerrar la etiqueta <script>
    return json.dumps(objeto, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def main():
    fuentes = cargar_fuentes()
    indicadores = cargar_indicadores(fuentes)
    comunas = cargar_comunas([i["id"] for i in indicadores])

    geo = cargar_geojson("comunas_biobio.geojson")
    provincias = cargar_geojson("provincias_biobio.geojson")
    cuts_mapa = {f["properties"]["cut"] for f in geo["features"]}
    faltan = [c["nombre"] for c in comunas if c["cut"] not in cuts_mapa]
    if faltan:
        raise ValueError(f"Estas comunas no tienen polígono en el mapa: {faltan}")

    config = dict(CONFIGURACION, fecha=date.today().strftime("%d-%m-%Y"))
    config["faltantes"] = buscar_faltantes(comunas, indicadores)
    for f in config["faltantes"]:
        print(f"Faltan datos: {f['nombre']} ({f['anio']}) en {len(f['comunas'])} de {len(comunas)} comunas")
    datos = {"comunas": comunas, "geo": geo, "prov": provincias}

    plantilla = (CARPETA / "plantilla.html").read_text(encoding="utf-8")
    pagina = (
        plantilla
        .replace("/*TITULO*/", config["titulo"])
        .replace("/*DATOS*/null", a_js(datos))
        .replace("/*CONFIG*/null", a_js(config))
        .replace("/*FUENTES*/null", a_js(fuentes))
        .replace("/*INDICADORES*/null", a_js(indicadores))
    )
    SALIDA.parent.mkdir(exist_ok=True)
    SALIDA.write_text(pagina, encoding="utf-8")
    print(f"Listo: {SALIDA} ({len(comunas)} comunas, {len(indicadores)} indicadores)")


if __name__ == "__main__":
    main()
