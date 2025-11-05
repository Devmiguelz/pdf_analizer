import os
import pandas as pd

# ============================================================
# 🧾 Generar informe resumen ESG (con carpeta 'informe')
# ============================================================
def generar_informe(resultados):
    """
    Recibe una lista de diccionarios con resultados individuales de cada categoría.
    Devuelve un DataFrame con el formato del informe resumen.
    """

    columnas = [
        "Componente",
        "Indicador GRI",
        "Dato (extracto)",
        "Escala (1–5)",
        "Justificación resumida",
        "Página"
    ]

    # Crear el DataFrame
    df = pd.DataFrame(resultados, columns=columnas)

    # Crear la carpeta "informe" si no existe
    carpeta_salida = "informe"
    os.makedirs(carpeta_salida, exist_ok=True)

    # Nombre del archivo
    nombre_archivo = os.path.join(carpeta_salida, "informe_resumen_ESG.xlsx")

    # Exportar a Excel
    df.to_excel(nombre_archivo, index=False)

    # Mostrar en pantalla el resumen
    print("\n" + "=" * 100)
    print("📊 RESUMEN FINAL DEL ANÁLISIS ESG")
    print("=" * 100)
    print(df.to_string(index=False))
    print("=" * 100)
    print(f"\n✅ Informe guardado en: {nombre_archivo}\n")

    return df


# ============================================================
# 🔍 Simulación de prueba
# ============================================================
if __name__ == "__main__":
    resultados_prueba = [
        {
            "Componente": "Ambiental",
            "Indicador GRI": "GRI 305-1/2/3 – Emisiones GEI",
            "Dato (extracto)": "330,24 t CO₂e, Alcance 1–3",
            "Escala (1–5)": 4,
            "Justificación resumida": "Reporta emisiones en los tres alcances, reducción frente a 2019, sin meta Net Zero declarada",
            "Página": 190
        },
        {
            "Componente": "Social",
            "Indicador GRI": "GRI 401-1 – Empleo",
            "Dato (extracto)": "28.624 empleos generados",
            "Escala (1–5)": 4,
            "Justificación resumida": "Alta generación de empleo, estabilidad laboral, sin metas de inclusión diferenciadas",
            "Página": "100–101"
        },
        {
            "Componente": "Gobernanza",
            "Indicador GRI": "GRI 205 – Anticorrupción",
            "Dato (extracto)": "403 funcionarios (94%) capacitados",
            "Escala (1–5)": 4,
            "Justificación resumida": "Cobertura alta de formación (>75% pero <95%)",
            "Página": 129
        },
    ]

    generar_informe(resultados_prueba)
