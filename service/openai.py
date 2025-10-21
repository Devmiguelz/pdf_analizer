from openai import OpenAI
import json

client = OpenAI()

def analizar_tendencia_categoria(texto: str, categoria: str):
    """
    Analiza un fragmento de texto y devuelve un JSON con los datos interanuales
    detectados (aumento, reducción o sin cambio).
    Funciona de manera genérica para cualquier categoría.
    """

    print(f"Realizando análisis de tendencia para la categoría: {categoria}")

    prompt = f"""
    Eres un analista de sostenibilidad experto en reportes GRI.

    Lee el siguiente texto relacionado con la categoría "{categoria}" y analiza 
    si aparecen valores numéricos asociados a años (por ejemplo 2019, 2020, 2021...).
    Usa esa información para determinar si hay un aumento o reducción entre los años consecutivos.

    Tu salida debe ser SIEMPRE un JSON con el formato exacto siguiente:

    {{
    "categoria": "{categoria}",
    "anio_inicial": <año base o null>,
    "valor_inicial": <número entero sin separadores o null>,
    "anio_final": <año comparado o null>,
    "valor_final": <número entero sin separadores o null>,
    "variacion": <porcentaje de cambio con dos decimales o null>,
    "tipo_cambio": "<aumento|reducción|sin_cambio|no_determinado>",
    "unidad": "<unidad si se detecta, por ejemplo kWh, m3, toneladas, %, etc. o null>"
    }}

    Reglas:
    - Si hay más de dos años, usa los dos más recientes.
    - Si no hay datos comparables, deja los valores en null.
    - Si hay texto con varios valores, elige los que correspondan al indicador principal de la categoría.
    - Calcula la variación como: ((valor_final - valor_inicial) / valor_inicial) * 100

    Texto a analizar:
    \"\"\"{texto}\"\"\"
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )

    # Asegurar salida JSON válida (limpia posibles envoltorios markdown)
    raw_content = response.choices[0].message.content.strip()

    # Elimina ```json o ``` si están presentes
    if raw_content.startswith("```"):
        raw_content = raw_content.strip("`")
        raw_content = raw_content.replace("json", "", 1).strip()

    # Buscar contenido JSON dentro de bloques con expresiones regulares
    import re
    match = re.search(r'\{[\s\S]*\}', raw_content)
    if match:
        raw_content = match.group(0)

    try:
        result = json.loads(raw_content)
    except json.JSONDecodeError:
        result = {
            "categoria": categoria,
            "error": "No se pudo interpretar el JSON",
            "raw": raw_content
        }

    return result
