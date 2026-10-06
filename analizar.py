# 1. Importamos pandas, la biblioteca para trabajar con tablas
import pandas as pd

# 2. Leemos el CSV y lo guardamos en una variable llamada "datos"
datos = pd.read_csv("datos/comunas.csv")

# 3. Mostramos la tabla completa
print(datos)

# 4. Buscamos la comuna con más pobreza multidimensional
fila = datos.loc[datos["pobreza_multi"].idxmax()]
print("Comuna con más pobreza:", fila["comuna"], "-", fila["pobreza_multi"], "%")

# 5. Calculamos el promedio de votos de Kast en estas comunas
print("Promedio Kast 2021:", round(datos["kast_2021"].mean(), 1), "%")
