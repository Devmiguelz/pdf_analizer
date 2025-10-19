import json
import os
import re
from pathlib import Path
from collections import defaultdict
import PyPDF2
from fuzzywuzzy import fuzz

class PDFSearcher:
    def __init__(self, json_path, pdf_folder):
        """
        Inicializa el buscador de PDFs
        
        Args:
            json_path: Ruta al archivo JSON con las categorías
            pdf_folder: Carpeta donde están los PDFs
        """
        self.pdf_folder = pdf_folder
        self.categorias = self.cargar_json(json_path)
        
    def cargar_json(self, json_path):
        """Carga el archivo JSON con las categorías"""
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def listar_pdfs(self):
        """Lista todos los PDFs en la carpeta"""
        pdfs = [f for f in os.listdir(self.pdf_folder) if f.endswith('.pdf')]
        return pdfs
    
    def seleccionar_pdf(self):
        """Permite al usuario seleccionar un PDF"""
        pdfs = self.listar_pdfs()
        
        if not pdfs:
            print("No se encontraron PDFs en la carpeta especificada.")
            return None
        
        print("\n" + "="*60)
        print("PDFs DISPONIBLES:")
        print("="*60)
        
        for idx, pdf in enumerate(pdfs, 1):
            print(f"{idx}. {pdf}")
        
        while True:
            try:
                seleccion = int(input("\nSeleccione el número del PDF a analizar: "))
                if 1 <= seleccion <= len(pdfs):
                    return os.path.join(self.pdf_folder, pdfs[seleccion - 1])
                else:
                    print("Número fuera de rango. Intente nuevamente.")
            except ValueError:
                print("Por favor ingrese un número válido.")
    
    def extraer_texto_pdf(self, pdf_path):
        """
        Extrae el texto del PDF por páginas
        
        Returns:
            dict: {numero_pagina: texto}
        """
        texto_por_pagina = {}
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_paginas = len(pdf_reader.pages)
                
                print(f"\nExtrayendo texto de {total_paginas} páginas...")
                
                for num_pagina in range(total_paginas):
                    try:
                        pagina = pdf_reader.pages[num_pagina]
                        texto = pagina.extract_text()
                        texto_por_pagina[num_pagina + 1] = texto.lower()  # Convertir a minúsculas
                    except Exception as e:
                        print(f"Error al extraer página {num_pagina + 1}: {e}")
                        texto_por_pagina[num_pagina + 1] = ""
                        
        except Exception as e:
            print(f"Error al abrir el PDF: {e}")
            return None
        
        return texto_por_pagina
    
    def buscar_en_texto(self, texto, variantes):
        """
        Busca variantes exactas (palabras o frases) en el texto completo.
        Retorna lista de coincidencias encontradas con la variante exacta.
        """
        if not isinstance(texto, str):
            return []

        texto = texto.lower()
        coincidencias = []

        for variante in variantes:
            if variante.lower() in texto:
                coincidencias.append((variante, texto.find(variante.lower())))

        return coincidencias

    def buscar_unidades(self, texto, unidades):
        """Busca unidades de medida en el texto"""
        encontradas = []
        for unidad in unidades:
            if unidad.lower() in texto:
                encontradas.append(unidad)
        return encontradas
    
    def buscar_contexto(self, texto, palabras_contexto):
        """
        Devuelve True solo si el texto contiene 2 o más variantes distintas Y 
        coinciden como palabras completas o fragmentos significativos (>=4 letras).
        """

        if not isinstance(texto, str):
            return False

        texto = texto.lower()
        encontradas = set()

        for palabra in palabras_contexto:
            palabra = palabra.lower()

            # ✅ Solo contar si la palabra tiene al menos 4 letras o aparece como palabra completa
            if len(palabra) >= 4:
                if palabra in texto:
                    encontradas.add(palabra)
            else:
                # ✅ Para palabras cortas como "uso" o "agua", buscar como palabra completa
                import re
                if re.search(rf"\b{palabra}\b", texto):
                    encontradas.add(palabra)

        return len(encontradas) >= 2

    def extraer_fragmento(self, texto, variante, contexto=100):

        """Extrae un fragmento de texto alrededor de la variante encontrada"""
        texto_lower = texto.lower()
        variante_lower = variante.lower()
        
        pos = texto_lower.find(variante_lower)
        if pos != -1:
            inicio = max(0, pos - contexto)
            fin = min(len(texto), pos + len(variante) + contexto)
            fragmento = texto[inicio:fin]
            # Limpiar el fragmento
            fragmento = ' '.join(fragmento.split())
            return fragmento
        return None
    
    def analizar_pdf(self, pdf_path):
        """
        Analiza el PDF completo buscando todas las categorías
        
        Returns:
            dict: Resultados estructurados por sección y categoría
        """
        texto_por_pagina = self.extraer_texto_pdf(pdf_path)
        
        if not texto_por_pagina:
            return None
        
        resultados = {}
        
        print("\n" + "="*60)
        print("ANALIZANDO DOCUMENTO...")
        print("="*60)
      
        for seccion, categorias in self.categorias.items():
            resultados[seccion] = {}
            
            for categoria_info in categorias:
                indicador = categoria_info['indicador']
                nombre = categoria_info['nombre']
                categoria = categoria_info['categoria']
                variantes = categoria_info['variantes']
                unidades = categoria_info.get('unidades', [])
                contexto = categoria_info.get('contexto', [])
                
              
                resultados[seccion][categoria] = {
                    'indicador': indicador,
                    'nombre': nombre,
                    'encontrado': False,
                    'paginas': [],
                    'coincidencias': [],
                    'unidades_encontradas': [],
                    'contexto_encontrado': [],
                    'fragmentos': []
                }
                
                for num_pagina, texto in texto_por_pagina.items():
                    coincidencias = self.buscar_en_texto(texto, variantes)

                    # ✅ Filtrar solo variantes únicas
                    variantes_unicas = list({v[0].lower() for v in coincidencias})

                    # ✅ Aceptar solo si hay 2 o más variantes distintas
                    if len(variantes_unicas) < 2:
                        continue  # ❌ Saltar esta página por insuficiente contexto

                    # ✅ Registrar solo las variantes únicas (evita duplicados)
                    resultados[seccion][categoria]['encontrado'] = True
                    resultados[seccion][categoria]['paginas'].append(num_pagina)
                    resultados[seccion][categoria]['coincidencias'].extend(variantes_unicas)
                    
            
                    # Buscar unidades
                    unidades_en_pagina = self.buscar_unidades(texto, unidades)
                    resultados[seccion][categoria]['unidades_encontradas'].extend(unidades_en_pagina)

                    # Registrar si cumple contexto múltiple
                    contexto_en_pagina = self.buscar_contexto(texto, categoria_info["contexto"])
                   
                   
                    if contexto_en_pagina:
                        resultados[seccion][categoria]['contexto_encontrado'].append(f"Página {num_pagina}")
                    # Extraer fragmento (usar la primera variante como punto de anclaje)
                    fragmento = self.extraer_fragmento(texto, variantes_unicas[0])
                    if fragmento:
                        resultados[seccion][categoria]['fragmentos'].append({
                            "pagina": num_pagina,
                            "texto": fragmento
                        })

        return resultados
    
    def generar_reporte(self, resultados, pdf_name):
        """Genera un reporte legible de los resultados"""
        
        print("\n" + "="*60)
        print(f"REPORTE DE ANÁLISIS: {pdf_name}")
        print("="*60)
        print("Variantes encontradas cortadas")
        for seccion, categorias in resultados.items():
            print(f"\n{'─'*60}")
            print(f"📁 SECCIÓN: {seccion}")
            print(f"{'─'*60}")
            
            for categoria, info in categorias.items():
                if info['encontrado']:
                    paginas_unicas = sorted(set(info['paginas']))
                    # variantes = set(info['coincidencias'])
                    # print(f"   🔍 Variantes encontradas nuevas: {', '.join(variantes)}")
                    # variantes_encontradas = set([v[0] for v in info['coincidencias']])
                    variantes_encontradas =set(info['coincidencias'])
                    
                    unidades_unicas = set(info['unidades_encontradas'])
                    contexto_unico = set(info['contexto_encontrado'])
                    
                    print(f"\n✅ {info['indicador']} - {info['nombre'].upper()}")
                    print(f"   Categoría: {categoria}")
                    print(f"   📄 Páginas: {', '.join(map(str, paginas_unicas))}")
                    print(f"   🔍 Variantes encontradas: {', '.join(variantes_encontradas)}")
                    
                    if unidades_unicas:
                        print(f"   📊 Unidades detectadas: {', '.join(unidades_unicas)}")
                    
                    if contexto_unico:
                        print(f"   🔗 Contexto relacionado: {', '.join(contexto_unico)}")
                    
                    # Mostrar primer fragmento como ejemplo
                    if info['fragmentos']:
                        primer_fragmento = info['fragmentos'][0]
                        print(f"\n   📝 Ejemplo (pág. {primer_fragmento['pagina']}):")
                        print(f"      {primer_fragmento['texto'][:200]}...")
                        
                else:
                    print(f"\n❌ {info['indicador']} - {info['nombre'].upper()}")
                    print(f"   Categoría: {categoria}")
                    print(f"   ⚠️  No se encontró información")
        
        # Resumen
        print(f"\n{'='*60}")
        print("📊 RESUMEN")
        print(f"{'='*60}")
        
        total_encontrados = 0
        total_categorias = 0
        
        for seccion, categorias in resultados.items():
            encontrados = sum(1 for cat in categorias.values() if cat['encontrado'])
            total = len(categorias)
            porcentaje = (encontrados / total * 100) if total > 0 else 0
            
            total_encontrados += encontrados
            total_categorias += total
            
            print(f"\n{seccion}:")
            print(f"  ✓ Encontrados: {encontrados}/{total} ({porcentaje:.1f}%)")
        
        porcentaje_global = (total_encontrados / total_categorias * 100) if total_categorias > 0 else 0
        print(f"\n{'─'*60}")
        print(f"GLOBAL: {total_encontrados}/{total_categorias} ({porcentaje_global:.1f}%)")
        print(f"{'─'*60}")
    
    def exportar_json(self, resultados, pdf_name):
        """Exporta los resultados a un archivo JSON"""
        output_file = f"resultados_{Path(pdf_name).stem}.json"
        
        # Limpiar los resultados para exportar (remover fragmentos muy largos)
        resultados_limpio = {}
        for seccion, categorias in resultados.items():
            resultados_limpio[seccion] = {}
            for categoria, info in categorias.items():
                resultados_limpio[seccion][categoria] = {
                    'indicador': info['indicador'],
                    'nombre': info['nombre'],
                    'encontrado': info['encontrado'],
                    'paginas': sorted(set(info['paginas'])),
                    'variantes_encontradas': list(set([v[0] for v in info['coincidencias']])),
                    'unidades_encontradas': list(set(info['unidades_encontradas'])),
                    'contexto_encontrado': list(set(info['contexto_encontrado'])),
                    'numero_menciones': len(info['paginas'])
                }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(resultados_limpio, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Resultados exportados a: {output_file}")
    
    def exportar_reporte_html(self, resultados, pdf_name):
        """Exporta un reporte visual en HTML"""
        output_file = f"reporte_{Path(pdf_name).stem}.html"
        
        # Construir el HTML en partes
        html_header = """<!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reporte de Análisis GRI</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
            h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
            h2 { color: #34495e; margin-top: 30px; }
            .seccion { background: #ecf0f1; padding: 15px; margin: 15px 0; border-radius: 5px; }
            .categoria { background: white; padding: 15px; margin: 10px 0; border-left: 4px solid #3498db; }
            .encontrado { border-left-color: #27ae60; }
            .no-encontrado { border-left-color: #e74c3c; }
            .badge { display: inline-block; padding: 3px 8px; margin: 2px; background: #3498db; color: white; border-radius: 3px; font-size: 12px; }
            .paginas { color: #e67e22; font-weight: bold; }
            .fragmento { background: #f8f9fa; padding: 10px; margin: 10px 0; border-radius: 3px; font-size: 14px; font-style: italic; }
            .resumen { background: #2c3e50; color: white; padding: 20px; margin-top: 30px; border-radius: 5px; }
            .stat { display: inline-block; margin: 10px 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Reporte de Análisis GRI</h1>
    """
        
        html = html_header + f"        <p><strong>Documento:</strong> {pdf_name}</p>\n"
        
        for seccion, categorias in resultados.items():
            html += f'        <div class="seccion"><h2>📁 {seccion}</h2>\n'
            
            for categoria, info in categorias.items():
                clase = "encontrado" if info['encontrado'] else "no-encontrado"
                icono = "✅" if info['encontrado'] else "❌"
                
                html += f'            <div class="categoria {clase}">\n'
                html += f'                <h3>{icono} {info["indicador"]} - {info["nombre"]}</h3>\n'
                html += f'                <p><strong>Categoría:</strong> {categoria}</p>\n'
                
                if info['encontrado']:
                    paginas = sorted(set(info['paginas']))
                    html += f'                <p class="paginas">📄 Páginas: {", ".join(map(str, paginas))}</p>\n'
                    
                    variantes = set(info['coincidencias'])

                    html += '                <p><strong>Variantes encontradas:</strong><br>\n'

                    for v in variantes:
                        html += f'                    <span class="badge">{v}</span>\n'

                    html += '                </p>\n'
                    
                    if info['unidades_encontradas']:
                        unidades = set(info['unidades_encontradas'])
                        html += '                <p><strong>Unidades:</strong><br>\n'
                        for u in unidades:
                            html += f'                    <span class="badge">{u}</span>\n'
                        html += '                </p>\n'
                    
                    if info['fragmentos']:
                        html += '                <p><strong>Ejemplo de contexto:</strong></p>\n'
                        fragmento = info['fragmentos'][0]
                        texto_fragmento = fragmento["texto"][:300].replace('<', '&lt;').replace('>', '&gt;')
                        html += f'                <div class="fragmento">Página {fragmento["pagina"]}: {texto_fragmento}...</div>\n'
                else:
                    html += '                <p>⚠️ No se encontró información para este indicador</p>\n'
                
                html += '            </div>\n'
            
            html += '        </div>\n'
        
        # Resumen
        total_encontrados = sum(1 for cat in sum([list(c.values()) for c in resultados.values()], []) if cat['encontrado'])
        total_categorias = sum(len(c) for c in resultados.values())
        porcentaje = (total_encontrados / total_categorias * 100) if total_categorias > 0 else 0
        
        html += '        <div class="resumen"><h2>📈 Resumen Global</h2>\n'
        html += f'            <div class="stat">Total indicadores: {total_categorias}</div>\n'
        html += f'            <div class="stat">Encontrados: {total_encontrados}</div>\n'
        html += f'            <div class="stat">Cobertura: {porcentaje:.1f}%</div>\n'
        html += '        </div>\n'
        html += '    </div>\n</body>\n</html>'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"📄 Reporte HTML exportado a: {output_file}")


def main():
    """Función principal"""
    
    print("="*60)
    print("ANALIZADOR DE PDFs CON CATEGORÍAS GRI")
    print("="*60)
    
    # Configuración
    JSON_PATH = "categorias_gri.json"  # Ruta a tu archivo JSON
    PDF_FOLDER = "./pdfs"  # Carpeta con los PDFs
    
    # Verificar que existan los archivos necesarios
    if not os.path.exists(JSON_PATH):
        print(f"❌ Error: No se encontró el archivo {JSON_PATH}")
        return
    
    if not os.path.exists(PDF_FOLDER):
        print(f"❌ Error: No se encontró la carpeta {PDF_FOLDER}")
        return
    
    # Crear el buscador
    searcher = PDFSearcher(JSON_PATH, PDF_FOLDER)
    
    # Seleccionar PDF
    pdf_path = searcher.seleccionar_pdf()
    
    if not pdf_path:
        return
    
    # Analizar PDF
    resultados = searcher.analizar_pdf(pdf_path)
    
    if resultados:
        # Generar reporte en consola
        searcher.generar_reporte(resultados, os.path.basename(pdf_path))
        
        # Exportar resultados
        print("\n" + "="*60)
        print("OPCIONES DE EXPORTACIÓN")
        print("="*60)
        print("1. Exportar a JSON")
        print("2. Exportar a HTML")
        print("3. Ambos")
        print("4. No exportar")
        
        opcion = input("\nSeleccione una opción (1-4): ")
        
        if opcion == "1":
            searcher.exportar_json(resultados, os.path.basename(pdf_path))
        elif opcion == "2":
            searcher.exportar_reporte_html(resultados, os.path.basename(pdf_path))
        elif opcion == "3":
            searcher.exportar_json(resultados, os.path.basename(pdf_path))
            searcher.exportar_reporte_html(resultados, os.path.basename(pdf_path))
    
    print("\n✨ Análisis completado")


if __name__ == "__main__":
    main()