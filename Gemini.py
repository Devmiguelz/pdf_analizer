import google.generativeai as genai
import os

# --- Configura la clave API ---
# os.environ["GEMINI_API_KEY"] = "TU_API_KEY_AQUI"
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
for m in genai.list_models():
    print(m.name)
# --- Inicia el modelo ---
model = genai.GenerativeModel( "models/gemini-2.5-flash")

print("✅ Conectado correctamente a Gemini (modelo: gemini-1.5-flash)")

while True:
    user_input = input("Tú: ")
    if user_input.lower() in ["salir", "exit", "quit"]:
        print("👋 Cerrando chat.")
        break

    try:
        response = model.generate_content(user_input)
        print("Gemini:", response.text)
    except Exception as e:
        print("⚠️ Error en la consulta:", e)
