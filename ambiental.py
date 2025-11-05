import os
import json
import time
import google.generativeai as genai
import pandas as pd
# === CONFIGURACIÓN INICIAL ===
# Asegúrate de tener configurada tu clave:
# setx GEMINI_API_KEY "tu_api_key_aqui"
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Modelo
modelo = genai.GenerativeModel("gemini-2.0-flash")

# === CONTROL DE LÍMITES (10 por minuto) ===
MAX_POR_MINUTO = 9
PETICIONES = 0
TIEMPO_INICIO = time.time()
informe = []

def controlar_limite():
    global PETICIONES, TIEMPO_INICIO
    PETICIONES += 1
    if PETICIONES >= MAX_POR_MINUTO:
        tiempo_transcurrido = time.time() - TIEMPO_INICIO
        if tiempo_transcurrido < 58:
            espera = 60 - tiempo_transcurrido
            print(f"Peticiones maximas por minuto {MAX_POR_MINUTO} Esperando {espera:.1f} segundos para no exceder el límite por minuto...")
            time.sleep(espera)
        PETICIONES = 0
        TIEMPO_INICIO = time.time()


# === CARGAR JSON DIMENSIONES ===
def cargar_json(carpeta="dimensiones"):
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
            print(f" Archivo no encontrado: {ruta}")
            datos[cat] = []
    return datos

# Nueva función para leer el JSON por dimensión (Ambiental, Social, Gobernanza)
# Función corregida
def leer_json_contexto(nombre_dimension):
    # nombre_dimension = "AMBIENTAL" / "SOCIAL" / "GOBERNANZA"
    ruta_json = os.path.join("contextos", nombre_dimension.lower() + ".json")
    print(f" Leyendo JSON de contexto desde: {ruta_json}")
    with open(ruta_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Retornar solo el diccionario dentro de la clave de la dimensión
    return data.get(nombre_dimension, {})

# === LEER CONTEXTO ===
def leer_contexto(nombre_archivo):
    ruta = os.path.join("contextos", nombre_archivo)
    if not os.path.exists(ruta):
        print(f" No se encontró el archivo de contexto: {ruta}")
        return ""
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


# === FUNCIÓN PRINCIPAL ===
def analizar(dimension_obj,componente,ruta_json):
    # datos = cargar_json()
    # dimensiones = datos.get(dimension, [])
    print(f"Total de items en dimensión: {len(dimension_obj)}")
    print(f"dimension {componente}" )
    # Cargar el JSON de contexto solo una vez por dimensión
   
    # print(dimension)
    for item in dimension_obj:
        categoria = item["categoria"]
        pregunta = item["pregunta"]
        archivo = item["contexto_archivo"]
        indicador = item["indicador"]
        print("\n" + "=" * 80)
        print(f"Indicador: {indicador}")
        print(f"Categoría: {categoria.upper()}")
        print(f"Pregunta: {pregunta}")
        print("-" * 80)

        ##contexto = leer_contexto(archivo)
         #Leer el JSON completo solo una vez por dimensión
        datos_dimension = leer_json_contexto(componente)
    
        clave_indicador = item["categoria"]  # coincide con la clave del JSON
        info_indicador = datos_dimension.get(clave_indicador, {})

        contexto = info_indicador.get("contexto", "")
        paginas = info_indicador.get("paginas", [])
        if not info_indicador:
            print("  No hay contexto disponible, se salta esta categoría.\n")
            continue

        print(f"Fragmento del contexto ({archivo}):\n")
        print(contexto[:400] + "...\n")

        confirmar = input("¿Deseas enviar esta pregunta a Gemini? (S/N): ").strip().lower()
        if confirmar != "s":
            print("  Saltando...\n")
            continue

        prompt = f"Contexto:\n{contexto}\n\nPregunta:\n{pregunta}"

        try:
            controlar_limite()


            # respuesta = modelo.generate_content(prompt)
            respuesta= f"si su pregunta :\n {pregunta} \nfue respondida con \n {prompt}"



            print("\n Respuesta de Gemini:\n")
            print(respuesta) 
            #es respuesta.text
            print("\nConsulta completada con éxito.\n")
            
            fila = {
                "Componente ": componente,
                "Indicador GRI": indicador,
                "Dato (extracto)": contexto,
                "Escala (1–5)": 1,  # Tentativo
                "Justificación resumida": respuesta,
                "Páginas": ", ".join(map(str, paginas))
            }

            print(" Indicador procesado:", fila)
            informe.append(fila)


        except Exception as e:
            print(f" Error al consultar Gemini: {e}")
            continue

    df = pd.DataFrame(informe)
    df.to_excel("informe/informe_resumen.xlsx", index=False)
    print("Informe guardado en 'informe/informe_resumen_ASG.xlsx'")


if __name__ == "__main__":
    print("===  Analizador Ambiental Gemini - Gener ===")
    print("Conectando con modelo gemini-2.0-flash...\n")
    categorias = cargar_json("categorias")
    print("Claves cargadas:", categorias.keys())
    print("Cantidad items AMBIENTAL:", len(categorias["AMBIENTAL"]))
  
    for categoria in ["AMBIENTAL", "SOCIAL", "GOBERNANZA"]:
        print(f"\n=== Analizando categoría: {categoria} ===")
        analizar(categorias[categoria],categoria,"contextos")