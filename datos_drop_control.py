from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import pandas as pd
import os

# === Configurar Selenium en modo headless ===
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

# === Inicializar navegador ===
driver = webdriver.Chrome(options=options)
driver.get("https://www.dropcontrol.com/new/login")
wait = WebDriverWait(driver, 15)

# === Paso 1: Aceptar cookies ===
checkbox = wait.until(EC.element_to_be_clickable((
    By.XPATH, "//p[contains(text(),'Acepto las cookies')]/input[@type='checkbox']"
)))
checkbox.click()

btn_aceptar = wait.until(EC.element_to_be_clickable((
    By.XPATH, "//a[contains(text(),'Aceptar') and contains(@class,'login_buttonAccept__FogzI')]"
)))
btn_aceptar.click()

# === Paso 2: Login ===
wait.until(EC.presence_of_element_located((By.ID, "username")))
driver.find_element(By.ID, "username").send_keys("evaluaciones@grupotrebol.pe")
driver.find_element(By.ID, "password").send_keys("cpv123456")
driver.find_element(By.CSS_SELECTOR, "a.login_btn__3iTcQ.login_submit__LVROK").click()

# === Paso 3: Esperar a que cargue el dashboard ===
wait.until(EC.presence_of_element_located((By.ID, "datosTemperaturaCampo")))

# === Paso 4: Extraer datos ===
import re

def limpiar_valor(valor):
    return float(re.sub(r"[^\d.]", "", valor)) if valor else None

Temperatura = limpiar_valor(driver.find_element(By.ID, "datosTemperaturaCampo").text)
Humedad_Relativa = limpiar_valor(driver.find_element(By.ID, "datosHumedadCampo").text)
Radiacion_Solar = limpiar_valor(driver.find_element(By.ID, "datosRadiacionCampo").text)
Velocidad_Viento = limpiar_valor(driver.find_element(By.ID, "datosVelVientoCampo").text)
Direccion_Viento = driver.find_element(By.ID, "datosDirVientoCampo").text.strip()
Lluvia = limpiar_valor(driver.find_element(By.ID, "datosPrecipitacionCampo").text)

# Limpiar y convertir Fecha
Fecha_Hora_raw = driver.find_element(By.ID, "datosFechaCampo").text.strip()
Fecha_Hora = pd.to_datetime(Fecha_Hora_raw, dayfirst=True, errors='coerce')

Hora_Ejecucion = datetime.now().strftime("%H:%M:%S")

# === NUEVO: Calcular Año y Semana ===
fecha_parseada = pd.to_datetime(Fecha_Hora, dayfirst=True, errors='coerce')
anio = fecha_parseada.year if not pd.isna(fecha_parseada) else None
semana = fecha_parseada.isocalendar().week if not pd.isna(fecha_parseada) else None

# === Paso 5: Guardar en Excel ===
datos = {
    'Fecha': [datetime.now()],
    'Año': [anio],
    'Sem': [semana],
    'Temperatura (ºC)': [Temperatura],
    'Humedad Relativa (%)': [Humedad_Relativa],
    'Radiación Solar (W/m²)': [Radiacion_Solar],
    'Velocidad de Viento Promedio (km/h)': [Velocidad_Viento],
    'Dirección de Viento Predominante': [Direccion_Viento],
    'Precipitación (mm)': [Lluvia],
    'Hora de Ejecución': [Hora_Ejecucion],  # <-- NUEVA COLUMNA
}

df_nuevo = pd.DataFrame(datos)

# === Guardar por día en carpeta específica ===
ruta_base = r"C:\\Users\\PC\\mi-app-humedad\\datos_dropcontrol"
os.makedirs(ruta_base, exist_ok=True)

nombre_archivo = datetime.now().strftime("%Y-%m-%d") + ".xlsx"
ruta_archivo = os.path.join(ruta_base, nombre_archivo)

if os.path.exists(ruta_archivo):
    df_existente = pd.read_excel(ruta_archivo)
    df_actualizado = pd.concat([df_existente, df_nuevo], ignore_index=True)
    df_actualizado.to_excel(ruta_archivo, index=False)
else:
    df_nuevo.to_excel(ruta_archivo, index=False)

# === Paso 6: Cerrar navegador ===
driver.quit()

# === Mostrar en consola ===
print("Temperatura:", Temperatura)
print("Humedad Relativa:", Humedad_Relativa)
print("Radiación Solar:", Radiacion_Solar)
print("Velocidad del Viento:", Velocidad_Viento)
print("Dirección del Viento:", Direccion_Viento)
print("Lluvia:", Lluvia)
print("Fecha y Hora:", Fecha_Hora)
print("Hora de Ejecución:", Hora_Ejecucion)

# === BLOQUE ADICIONAL: Consolidado ===
carpeta_origen = r"C:\\Users\\PC\\mi-app-humedad\datos_dropcontrol"
archivo_consolidado = r"C:\\Users\\PC\\mi-app-humedad\\estacion_metereologica.xlsx"

# Buscar todos los archivos .xlsx en la carpeta de origen
todos_los_archivos = [
    os.path.join(carpeta_origen, f)
    for f in os.listdir(carpeta_origen)
    if f.endswith(".xlsx")
]

# Leer y concatenar todos los DataFrames
df_consolidado = pd.concat([pd.read_excel(f) for f in todos_los_archivos], ignore_index=True)

# Guardar consolidado
df_consolidado.to_excel(archivo_consolidado, index=False)
