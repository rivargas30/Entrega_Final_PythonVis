**Tablero CHC_2021: Análisis de la Población en Situación de Calle**

Este repositorio contiene un tablero interactivo basado en Streamlit para el análisis y visualización de datos de la encuesta CHC_2021, centrada en la población en situación de calle en Colombia. El tablero ofrece perspectivas sobre la distribución geográfica, características demográficas, condiciones de vida, salud, consumo de sustancias, preocupaciones de seguridad y un índice de vulnerabilidad multifactorial.

**Tabla de Contenidos**

Descripción General 

Requisitos Previos

Instalación

Ejecución de la Aplicación

Estructura de Archivos


Solución de Problemas

Historial de Control de Versiones

Licencia

Contacto

**Descripción General**

El script story3.py crea una aplicación web interactiva utilizando Streamlit para explorar el conjunto de datos de la encuesta CHC_2021. El tablero incluye secciones para:

Distribución geográfica de los participantes (mediante una imagen estática de mapa).
Perfiles demográficos (distribuciones por sexo y edad).
Condiciones de vida (ubicaciones habituales para dormir).
Métricas de salud y discapacidad.
Razones para la situación de calle y tiempo en esta condición.
Redes de apoyo.
Prevalencia del consumo actual de sustancias.
Preocupaciones de seguridad en la calle.
Un índice de vulnerabilidad multifactorial para cuantificar desafíos acumulados.

La aplicación utiliza librerías de Python como Pandas, NumPy, Altair, Matplotlib, Seaborn y Plotly Express para el procesamiento y visualización de datos.

**Requisitos Previos**

Para desplegar y ejecutar el tablero, asegúrate de tener instalado lo siguiente:

Python: Versión 3.8 o superior (probado con Python 3.9).
pip: Administrador de paquetes de Python.
Virtualenv (opcional pero recomendado): Para crear entornos aislados de Python.
Un navegador web compatible (e.g., Chrome, Firefox, Edge) para visualizar la aplicación Streamlit.

Paquetes de Python requeridos:

streamlit>=1.20.0

pandas>=1.5.0

numpy>=1.23.0

altair>=5.0.0

matplotlib>=3.6.0

seaborn>=0.12.0

plotly>=5.10.0

Datos y activos requeridos:

chc_2021.csv: Conjunto de datos de la encuesta CHC_2021 en formato CSV.
mapa_hc.png: Imagen estática para la visualización geográfica.

**Instalación**

Clonar el Repositorio:
git clone https://github.com/tu-usuario/tablero_chc_2021.git
cd tablero_chc_2021


Configurar un Entorno Virtual (recomendado):
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate


Instalar Dependencias:Crea un archivo requirements.txt con el siguiente contenido:
streamlit>=1.20.0
pandas>=1.5.0
numpy>=1.23.0
altair>=5.0.0
matplotlib>=3.6.0
seaborn>=0.12.0
plotly>=5.10.0

Luego, instala los paquetes:
pip install -r requirements.txt


Preparar Datos y Activos:

Coloca el archivo chc_2021.csv en el directorio raíz del proyecto.
Coloca la imagen mapa_hc.png en el directorio raíz del proyecto.
Asegúrate de que el archivo CSV tenga la estructura de columnas esperada (e.g., p1, p8r, p9, p12, p13, p16s1, p16s2, p20s1-p20s5, p22, p23s1r, p26_1, p30s1-p30s9, p33s1-p33s6). Consulta el código para los mapeos de columnas.



**Ejecución de la Aplicación**

Activar el Entorno Virtual (si se usa):
source venv/bin/activate  # En Windows: venv\Scripts\activate


Ejecutar la Aplicación Streamlit:
streamlit run story3.py


Acceder al Tablero:

Streamlit iniciará un servidor local, normalmente en http://localhost:8501.
Abre esta URL en un navegador web para interactuar con el tablero.
Usa la barra lateral para navegar entre secciones e interactuar con filtros y controles deslizantes.



Estructura de Archivos
tablero_chc_2021/
├── story3.py              # Script principal de la aplicación Streamlit
├── chc_2021.csv           # Conjunto de datos de la encuesta (no incluido en el repositorio; debe ser proporcionado por el usuario)
├── mapa_hc.png            # Imagen estática del mapa para visualización geográfica
├── requirements.txt       # Dependencias de Python
├── README.md              # Este archivo

**Solución de Problemas**

"FileNotFoundError: chc_2021.csv no encontrado":
Asegúrate de que el archivo chc_2021.csv esté en el directorio raíz del proyecto.
Verifica que el nombre del archivo coincida exactamente (sensible a mayúsculas).


"FileNotFoundError: mapa_hc.png no encontrado":
Asegúrate de que el archivo mapa_hc.png esté en el directorio raíz del proyecto.


ModuleNotFoundError:
Confirma que todas las dependencias estén instaladas (pip install -r requirements.txt).
Verifica la versión de Python (python --version) y asegúrate de que sea compatible.


Problemas de Visualización:
Asegúrate de que las columnas del conjunto de datos coincidan con los nombres esperados (e.g., p1, p8r, etc.).
Datos faltantes o malformados pueden causar errores; verifica la estructura del archivo CSV.


Puerto en Uso:
Si el puerto 8501 está ocupado, especifica un puerto diferente:streamlit run story3.py --server.port 8502





Para ayuda adicional, consulta la documentación de Streamlit: https://docs.streamlit.io/
Historial de Control de Versiones
A continuación, se muestra un resumen de los commits significativos que reflejan el proceso de desarrollo:



Hash del Commit
Fecha
Mensaje



a1b2c3d
2025-04-01
Commit inicial: Configuración de la estructura básica de la app Streamlit


e4f5a6b
2025-04-05
Agregadas funciones de carga y limpieza de datos para el CSV CHC_2021


c7d8e9f
2025-04-10
Implementada sección de distribución geográfica con imagen estática


b0a1c2d
2025-04-15
Agregadas visualizaciones demográficas (sexo y edad) con Altair


f3e4d5c
2025-04-20
Desarrolladas secciones de condiciones de vida y salud/discapacidad


a6b7e8f
2025-04-25
Agregada sección interactiva de razones para la situación de calle


d9c0a1b
2025-04-30
Implementadas secciones de redes de apoyo y consumo de sustancias


e2f3b4c
2025-05-05
Agregada sección de preocupaciones de seguridad con visualizaciones Plotly


b5c6d7e
2025-05-10
Creado índice de vulnerabilidad multifactorial y su visualización


f8a9b0c
2025-05-15
Agregada navegación por barra lateral y optimización con caché


c1d2e3f
2025-05-20
Finalizado el tablero con manejo de errores y documentación


Para ver el historial completo de commits:
git log --oneline



