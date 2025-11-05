import json
import os
import pandas as pd

def cargar_json_categorias(carpeta="dimensiones"):
    rutas = {
        "AMBIENTAL": os.path.join(carpeta, "ambiental.json"),
        "SOCIAL": os.path.join(carpeta, "social.json"),
        "GOBERNANZA": os.path.join(carpeta, "gobernanza.json")
    }
    datos = {}
    for cat, ruta in rutas.items():
        if os.path.exists(ruta):
            with open(ruta, "r", encoding="utf-8") as f:
                datos[cat] = json.load(f)[cat]
        else:
            print(f"Archivo no encontrado: {ruta}")
            datos[cat] = []
    return datos

def cargar_json_contexto(dimension, carpeta="contextos"):
    ruta_json = os.path.join(carpeta, dimension.lower() + ".json")
    if not os.path.exists(ruta_json):
        print(f" Contexto no encontrado: {ruta_json}")
        return {}
    with open(ruta_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get(dimension.upper(), {})

def pre_filtrar_contextos(categorias, carpeta_contextos="contextos", min_variantes=2):
    filas = []

    for dim, items in categorias.items():
        contexto_json = cargar_json_contexto(dim, carpeta_contextos)

        for item in items:
            nombre_indicador = item["categoria"].lower()
            info_contexto = contexto_json.get(nombre_indicador, {})
            contexto_texto = info_contexto.get("contexto", "")
                        # Conteo de palabras
            num_palabras = len(contexto_texto.split())
            variantes = [v.lower() for v in item.get("variantes", [])]
            presentes = [v for v in variantes if v in contexto_texto.lower()]

            valido = len(presentes) >= min_variantes

            fila = {
                "Dimensión": dim,
                "Indicador": item["indicador"],
                "Nombre": item["nombre"],
                "Pregunta": item["pregunta"],
                "Contexto válido": "Sí" if valido else "No",
                "Variantes encontradas": ", ".join(presentes),
                "Número variantes encontradas": len(presentes),
                "Total variantes": len(variantes),
                "Páginas": ", ".join(map(str, info_contexto.get("paginas", []))),
                "Contexto extracto": contexto_texto[:1000] + "..." if contexto_texto else "",
                "Palabras": num_palabras
            }

            filas.append(fila)

    return filas

def guardar_csv(filas, nombre_archivo="reporte_contextos.csv"):
    df = pd.DataFrame(filas)
    carpeta_salida = os.path.join('.', "prefiltro")
    os.makedirs(carpeta_salida, exist_ok=True)  # Crea la carpeta si no existe

    archivo_ruta_salida = os.path.join(carpeta_salida,nombre_archivo)
    df.to_csv(archivo_ruta_salida, index=False, encoding="utf-8-sig")
    print(f" CSV generado: {nombre_archivo}")

# === EJEMPLO DE USO ===
if __name__ == "__main__":
    categorias = cargar_json_categorias()
    filas = pre_filtrar_contextos(categorias, min_variantes=1)
    guardar_csv(filas)
