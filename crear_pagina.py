import pandas as pd

datos = pd.read_csv("datos/comunas.csv")
tabla = datos.to_html(index=False)

html = f"""<!doctype html>
<html lang="es">
<head><meta charset="utf-8"><title>Brújula Biobío</title></head>
<body>
<h1>Brújula Biobío</h1>
<p>Datos electorales y sociales de comunas del Biobío.</p>
{tabla}
</body>
</html>"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Listo: se creó index.html")