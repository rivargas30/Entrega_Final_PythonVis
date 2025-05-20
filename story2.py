# Cargar streamlit para crear la aplicación web interactiva
import streamlit as st
# Leer un archivo CSV para cargar los datos
import pandas as pd
# Librerías para crear visualizaciones
import altair as alt
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import plotly.express as px

# --- Configuración de la Página ---
# Configura el layout de la página a 'wide' para usar más espacio horizontal
# y establece el título que aparecerá en la pestaña del navegador.
st.set_page_config(layout="wide", page_title="Habitantes de calle: algunos indicadores")


# --- Cargar el archivo CSV ---
# Usa caché (@st.cache_data) para que la carga de datos solo ocurra
# la primera vez que se ejecuta la aplicación o cuando el archivo cambia.
# Esto hace que el dashboard sea mucho más rápido al interactuar con él.
@st.cache_data
def load_data(filepath):
    """
    Carga datos desde un archivo CSV especificado por filepath.
    Incluye manejo básico de errores si el archivo no se encuentra.
    Limpia los nombres de las columnas para facilitar su uso en Python,
    reemplazando espacios y puntos por guiones bajos y convirtiendo a minúsculas.
    """
    try:
        df = pd.read_csv(filepath)
        # Limpiar nombres de columnas: reemplazar espacios y puntos por guiones bajos, convertir a minúsculas
        df.columns = df.columns.str.replace('[ .]', '_', regex=True).str.lower()
        st.success(f"Archivo '{filepath}' cargado exitosamente.")
        return df
    except FileNotFoundError:
        st.error(f"Error: El archivo '{filepath}' no fue encontrado. Asegúrate de que esté en la ubicación correcta.")
        return pd.DataFrame() # Retorna un DataFrame vacío en caso de error


# Carga el DataFrame usando la función con caché
df = load_data('chc_2021.csv')

# --- Definir Mapeos y Etiquetas (Centralizados) ---
# Estos diccionarios se utilizan para traducir los códigos numéricos o abreviaturas
# del dataset a etiquetas más comprensibles y descriptivas para las visualizaciones y el texto.
# Asegurarse de que las claves de los mapeos coincidan con los nombres de columnas transformados (minúsculas, guiones bajos).
sex_mapping = {1: 'Hombre', 2: 'Mujer'}
p12_mapping = {1: 'En este municipio', 2: 'Otro municipio', 3: 'Otro país'}
p13_mapping = {1: 'Calle', 2: 'Dormitorio', 3: 'Institución'}
p16_mapping = {1: 'No puede hacerlo', 2: 'Mucha dificultad', 3: 'Con dificultad', 4: 'Sin esfuerzo'}
p20_preguntas = {
    'p20s1': 'Hipertensión', 'p20s2': 'Diabetes', 'p20s3': 'Cáncer',
    'p20s4': 'Tuberculosis', 'p20s5': 'VIH-SIDA'
}
p22_etiquetas = {
    1: "Consumo de sustancias psicoactivas", 2: "Por gusto personal",
    3: "Amenaza o riesgo para su vida", 4: "Influencia de otras personas",
    5: "Dificultades económicas", 6: "Falta de trabajo",
    7: "Conflictos familiares", 8: "Abuso sexual",
    9: "Siempre ha vivido en la calle", 10: "Víctima del conflicto armado",
    11: "Otra"
}
p26_etiquetas = {
    1: "Familiar", 2: "Amigos", 3: "Instituciones oficiales",
    4: "Instituciones/organizaciones privadas", 5: "Organizaciones religiosas",
    6: "Otros"
}

# Mapeo para las columnas de consumo de sustancias (P30S - Actual Consumption)
substance_cols_mapping_current = {
    'p30s1': 'Cigarrillo', 'p30s2': 'Alcohol', 'p30s3': 'Marihuana',
    'p30s4': 'Inhalantes', 'p30s5': 'Cocaína', 'p30s6': 'Basuco',
    'p30s7': 'Heroína', 'p30s8': 'Pepas', 'p30s9': 'Otras'
}

# Mapeo para las columnas de seguridad en la calle (P33S)
security_factors_mapping = {
    'p33s1': 'Persecución por integrantes de olla',
    'p33s2': 'Ser forzado a cumplir tareas contra su voluntad',
    'p33s3': 'Abuso policial',
    'p33s4': 'Problemas con grupos juveniles (Barras Bravas, Calvos)',
    'p33s5': 'Problemas con la comunidad',
    'p33s6': 'Otra'
}

# Mapeo de códigos de departamento a nombres, basado en el archivo departamentos_2012.pdf
# Se crea un diccionario manualmente a partir de la información extraída del PDF.
department_code_to_name = {
    '05': 'Antioquia', '08': 'Atlántico', '17': 'Caldas', '68': 'Santander',
    '76': 'Valle del Cauca', '91': 'Amazonas', '81': 'Arauca', '11': 'Bogotá D.C.',
    '13': 'Bolivar', '15': 'Boyacá', '18': 'Caquetá', '85': 'Casanare',
    '19': 'Cauca', '20': 'Cesar', '27': 'Chocó', '23': 'Córdoba',
    '25': 'Cundinamarca', '94': 'Guainía', '95': 'Guaviare', '41': 'Huila',
    '44': 'La Guajira', '47': 'Magdalena', '50': 'Meta', '52': 'Nariño',
    '54': 'Norte de Santander', '86': 'Putumayo', '63': 'Quindío', '66': 'Risaralda',
    '88': 'San Andrés', '70': 'Sucre', '73': 'Tolima', '97': 'Vaupés', '99': 'Vichada'
}


# --- Calcular Indicador de Vulnerabilidad ---
# Este cálculo se realiza una vez al cargar los datos para definir un indicador
# que suma diferentes factores de vulnerabilidad reportados por cada persona.
# Un puntaje más alto indica mayor acumulación de desafíos.
# Asegura que df esté cargado y no vacío antes de calcular
if not df.empty:
    # 1. Alguna Enfermedad (P20S)
    # Verifica si el participante reportó tener alguna de las enfermedades listadas (código 1).
    health_cols = list(p20_preguntas.keys())
    existing_health_cols = [col for col in health_cols if col in df.columns]
    has_health_issue = pd.Series(False, index=df.index)
    if existing_health_cols:
        # .isin([1]) verifica si el valor es 1. .any(axis=1) verifica si es True en *alguna* de las columnas de salud por fila.
        # .fillna(False) trata los NaNs en las columnas originales como si no tuvieran la enfermedad.
        has_health_issue = df[existing_health_cols].isin([1]).any(axis=1).fillna(False)

    # 2. Alguna Discapacidad Sensorial/Comunicativa (P16S)
    # Verifica si el participante reportó mucha dificultad o imposibilidad para oír o hablar (códigos < 4).
    has_disability = pd.Series(False, index=df.index)
    p16s1_exists = 'p16s1' in df.columns
    p16s2_exists = 'p16s2' in df.columns
    if p16s1_exists or p16s2_exists:
        # Rellena NaNs con un valor >= 4 para que no cuenten como dificultad/discapacidad.
        # Asegura que la columna sea numérica para la comparación.
        p16s1_numeric = pd.to_numeric(df['p16s1'], errors='coerce').fillna(5) if p16s1_exists else pd.Series(5, index=df.index)
        p16s2_numeric = pd.to_numeric(df['p16s2'], errors='coerce').fillna(5) if p16s2_exists else pd.Series(5, index=df.index)
        # (p16s1_numeric < 4) | (p16s2_numeric < 4) verifica si hay dificultad/no puede (<4) en *cualquiera* de las dos columnas.
        has_disability = (p16s1_numeric < 4) | (p16s2_numeric < 4)

    # 3. Consumo Actual de Sustancias (P30S)
    # Verifica si el participante reportó consumir actualmente alguna sustancia (código 1).
    substance_cols_list = list(substance_cols_mapping_current.keys())
    existing_substance_cols = [col for col in substance_cols_list if col in df.columns]
    consumes_substances = pd.Series(False, index=df.index)
    if existing_substance_cols:
        # .isin([1]).any(axis=1) verifica si hay un '1' en *alguna* columna de sustancia por fila.
        # .fillna(False) trata los NaNs como no consumo.
        consumes_substances = df[existing_substance_cols].isin([1]).any(axis=1).fillna(False)

    # 4. Seguridad Afectada (P33S)
    # Verifica si el participante reportó que su seguridad en la calle fue afectada por algún factor (código 1).
    security_cols_list = list(security_factors_mapping.keys())
    existing_security_cols = [col for col in security_cols_list if col in df.columns]
    security_affected = pd.Series(False, index=df.index)
    if existing_security_cols:
        # .isin([1]).any(axis=1) verifica si hay un '1' en *alguna* columna de seguridad por fila.
        # .fillna(False) trata los NaNs como no afectado.
        security_affected = df[existing_security_cols].isin([1]).any(axis=1).fillna(False)

    # 5. Duerme en la Calle (P13)
    # Verifica si el participante reportó que duerme habitualmente en la calle (código 1).
    lives_on_street = pd.Series(False, index=df.index)
    if 'p13' in df.columns:
         # Asegura que P13 sea numérico antes de comparar, rellena NaNs con 0 u otro código que no sea '1'.
        p13_numeric = pd.to_numeric(df['p13'], errors='coerce').fillna(0)
        lives_on_street = (p13_numeric == 1) # True si P13 es 1

    # Calcula el puntaje de vulnerabilidad sumando las series booleanas (True=1, False=0).
    # Asegura que todas las series tengan el mismo índice que df.
    # Añade verificaciones de existencia de columna antes de sumar.
    score_components = []
    if not has_health_issue.empty: score_components.append(has_health_issue.astype(int))
    if not has_disability.empty: score_components.append(has_disability.astype(int))
    if not consumes_substances.empty: score_components.append(consumes_substances.astype(int))
    if not security_affected.empty: score_components.append(security_affected.astype(int))
    if not lives_on_street.empty: score_components.append(lives_on_street.astype(int))

    if score_components:
        # Suma los componentes existentes para obtener el puntaje total de vulnerabilidad por fila
        vulnerability_score = sum(score_components)
        # Almacena el puntaje en una nueva columna del dataframe
        df['_vulnerability_score'] = vulnerability_score
        # Calcula la distribución de los puntajes (cuántas personas tienen cada puntaje)
        vulnerability_counts = df['_vulnerability_score'].value_counts().sort_index().reset_index()
        vulnerability_counts.columns = ['Score', 'Frequency']
    else:
        st.warning("No se pudieron calcular los componentes del indicador de vulnerabilidad debido a la falta de columnas clave.")
        vulnerability_counts = pd.DataFrame() # Asegura que vulnerability_counts esté definido incluso si está vacío

else:
    st.error("El DataFrame no pudo ser cargado. Algunas secciones del dashboard no estarán disponibles.")
    vulnerability_counts = pd.DataFrame() # Asegura que vulnerability_counts esté definido


# --- Sidebar Navigation ---
with st.sidebar:
    # Cambiar el título de la barra lateral
    st.title("Habitantes de calle: algunos indicadores")
    st.write("Explora diferentes aspectos de la población encuestada.")

    # Crea un selectbox para la navegación, incluyendo la nueva sección
    page_selection = st.selectbox(
        "Ir a...",
        [
            "Inicio y Contexto", # Renombrado para storytelling
            "Tratamiento de Datos Faltantes y Atípicos", # Nueva Sección
            "Distribución Geográfica", # Eliminado código P1 del título
            "Características Demográficas", # Eliminado códigos P del título
            "Condiciones de Vida", # Eliminado códigos P del título
            "Salud y Discapacidad", # Eliminado códigos P del título
            "Razones y Tiempo en Calle", # Renombrado y eliminado códigos P
            "Fuentes de Ayuda", # Eliminado código P del título
            "Consumo de Sustancias", # Renombrado y eliminado códigos P
            "Seguridad en la Calle", # Eliminado código P del título
            "Indicador de Vulnerabilidad"
        ]
    )

    st.markdown("---") # Añade un separador visual
    # Actualizar el texto del pie de página
    st.write("Análisis basado en datos de la encuesta CHC_2021.")


# --- Área de Contenido Principal ---

# Verifica si el dataframe se cargó exitosamente antes de mostrar el contenido principal
if not df.empty:

    # Cambiar el título principal del dashboard
    st.title('Habitantes de calle: algunos indicadores')
    st.markdown("---") # Separador visual después del título principal

    # --- Sección: Inicio y Contexto ---
    if page_selection == "Inicio y Contexto":
        st.header("Inicio: Comprendiendo a los Habitantes de Calle")
        st.markdown("""
            Bienvenido a este espacio dedicado a explorar los datos de la encuesta CHC_2021,
            una valiosa fuente de información sobre la población habitante de calle en Colombia.
            Este dashboard busca arrojar luz sobre las diversas dimensiones de la vida
            de estas personas, desde su lugar de origen y condiciones de vida, hasta
            sus desafíos de salud, las razones que los llevaron a la calle y las redes
            de apoyo con las que cuentan.

            Navega a través de las secciones en el menú de la izquierda para visualizar
            diferentes indicadores y comprender mejor el contexto y las realidades que
            enfrenta esta población.

            Aquí puedes ver un vistazo inicial a la estructura de los datos con los que trabajamos:
        """)
        st.subheader('Primeros Registros del Conjunto de Datos')
        st.dataframe(df.head()) # Usa dataframe para una mejor visualización
        st.write(f"El conjunto de datos cargado contiene **{df.shape[0]} filas** (participantes) y **{df.shape[1]} columnas** (variables).")


    # --- Sección: Tratamiento de Datos Faltantes y Atípicos ---
    elif page_selection == "Tratamiento de Datos Faltantes y Atípicos":
        st.header("Tratamiento de Datos Faltantes y Atípicos")
        st.markdown("""
            En el análisis de cualquier conjunto de datos, especialmente aquellos que provienen de encuestas en contextos complejos como este,
            es común encontrar valores faltantes (datos que no fueron registrados) y datos atípicos (valores que se desvían significativamente
            de la mayoría). Es crucial abordar estos aspectos para asegurar que los análisis y visualizaciones sean lo más precisos y representativos posible.

            ### Datos Faltantes (NaNs)

            Los valores faltantes en este conjunto de datos se han manejado de diferentes maneras, dependiendo del tipo de análisis:

            * **Conteo y Porcentajes:** Para gráficos de distribución y porcentajes (como en salud, consumo de sustancias, o seguridad), los valores faltantes
                (`NaN`) generalmente se excluyen del denominador. Esto significa que los porcentajes se calculan sobre el total de *respuestas válidas* para esa pregunta específica,
                no sobre el total de participantes en la encuesta. Esto se logra típicamente usando `.value_counts()` que por defecto no incluye NaNs,
                o calculando sobre `.dropna()` subconjuntos de datos relevantes para la pregunta.
            * **Cálculos Numéricos:** Para columnas que representan valores numéricos (como la edad o el tiempo en calle), los valores no numéricos o faltantes
                se convierten a `NaN` (Not a Number) utilizando `pd.to_numeric(errors='coerce')` y luego se eliminan (`dropna()`) antes de calcular estadísticas
                como promedios, medianas o para la construcción de histogramas. Este enfoque evita que los valores inválidos afecten los cálculos agregados.
            * **Indicador de Vulnerabilidad:** En el cálculo del indicador multifactorial, los valores faltantes en las columnas componentes se tratan
                implícitamente como "no presentes" o "no reportados" en esa categoría de vulnerabilidad para ese participante. Por ejemplo, si la información sobre una enfermedad está faltante para un individuo, no se considera que esa persona tenga esa enfermedad *para el propósito de sumar puntos en el indicador específico de vulnerabilidad*.

            ### Datos Atípicos

            Los datos atípicos pueden distorsionar las estadísticas y las visualizaciones, especialmente en variables numéricas con rangos amplios.

            * **Identificación y Manejo:** Para variables como el "Tiempo Viviendo en la Calle" (P23S1R), donde pueden existir valores extremos (personas que llevan muchísimos años en la calle), hemos utilizado
                `pd.to_numeric(errors='coerce').dropna()` para asegurar que solo se procesen números válidos. No se han eliminado atípicos de forma automática, ya que pueden representar realidades importantes de la población habitante de calle y su experiencia de cronicidad.
            * **Visualización Interactiva:** En la sección de "Razones y Tiempo en Calle", se proporciona un **control deslizante (slider)** que permite al usuario
                explorar la distribución del tiempo en la calle dentro de un rango de años específico. Esto ayuda a visualizar la forma principal de la distribución
                sin la influencia potencial de valores atípicos muy altos, o a enfocarse precisamente en esos rangos extremos si se desea. Esta interactividad permite al usuario decidir cómo quiere ver los datos en diferentes escalas de tiempo.

            Este enfoque busca ofrecer una visión clara de los patrones generales en los datos, al tiempo que se reconoce la heterogeneidad dentro de la población encuestada y se permite cierta exploración interactiva de rangos específicos.
        """)


    # --- Sección: Distribución Geográfica (P1) ---
    elif page_selection == "Distribución Geográfica":
        st.header('Distribución de Participantes por Departamento')
        st.markdown("""
            Comprender dónde se realizó la encuesta nos da una idea del alcance geográfico del estudio y la distribución de la población habitante de calle encuestada en diferentes regiones de Colombia.
            Este gráfico muestra la cantidad de participantes reportados en cada departamento donde se llevó a cabo la recolección de datos (basado en la pregunta P1).

            Utilizamos un mapeo de códigos a nombres de departamento basado en información de referencia para presentar los resultados de forma más clara.
        """)
        # Verifica si la columna 'p1' existe en el dataframe
        if 'p1' in df.columns:
            # Cuenta la frecuencia de cada código de departamento
            chart_data_p1 = df['p1'].value_counts().reset_index()
            chart_data_p1.columns = ['Departamento_Code', 'Count']

            # Convierte el código de departamento a string para poder usar el mapeo (las claves del dict son strings)
            chart_data_p1['Departamento_Code_Str'] = chart_data_p1['Departamento_Code'].astype(str).str.zfill(2) # Asegura dos dígitos si es necesario

            # Mapea los códigos a nombres de departamento usando el diccionario
            # Usa .get(code, f'Código {code}') para manejar códigos que puedan no estar en el mapeo
            chart_data_p1['Departamento_Name'] = chart_data_p1['Departamento_Code_Str'].map(department_code_to_name).fillna(chart_data_p1['Departamento_Code_Str'].apply(lambda x: f'Código {x}'))


            # Crea un gráfico de barras usando Altair
            chart_p1 = alt.Chart(chart_data_p1).mark_bar().encode(
                # Usa el nombre del departamento en el eje X, ordenado por frecuencia descendente
                x=alt.X('Departamento_Name:O', sort='-y', title='Departamento'),
                y=alt.Y('Count', title='Número de Participantes'),
                # Colorea por nombre de departamento (o código si el nombre no se encuentra)
                color=alt.Color('Departamento_Name:N', scale=alt.Scale(scheme='pastel1'), legend=None),
                # Muestra nombre, código y conteo en el tooltip
                tooltip=['Departamento_Name', 'Departamento_Code', 'Count']
            ).properties(title='Distribución de Participantes por Departamento').interactive() # Permite interactividad (zoom, pan)
            st.altair_chart(chart_p1, use_container_width=True) # Muestra el gráfico ajustando al ancho del contenedor
        else:
            st.warning("La columna de código de departamento ('p1') no se encontró en el archivo CSV para este análisis.")


    # --- Sección: Características Demográficas (Sexo P9 y Edades P8R) ---
    elif page_selection == "Características Demográficas":
        st.header('Retrato de la Población: Sexo y Edades')
        st.markdown("""
            ¿Quiénes son las personas que viven en la calle? Explorar su distribución por sexo y edad nos ayuda a perfilar demográficamente a la población encuestada.
            Estos gráficos presentan la proporción de hombres y mujeres, y la distribución de edades, ofreciendo una instantánea de la estructura demográfica de los participantes.
        """)

        st.subheader('Distribución por Sexo')
        st.write('📊 Este gráfico muestra la proporción de hombres y mujeres que participaron en la encuesta, según lo reportado en la pregunta P9.')
        # Verifica si la columna 'p9' existe
        if 'p9' in df.columns:
            # Cuenta la frecuencia de cada código de sexo
            chart_data_sex = df['p9'].value_counts().reset_index()
            chart_data_sex.columns = ['p9_code', 'Count']
            # Filtra códigos no esperados que no estén en el mapeo
            chart_data_sex = chart_data_sex[chart_data_sex['p9_code'].isin(sex_mapping.keys())]
            # Mapea los códigos a etiquetas descriptivas
            chart_data_sex['Sexo'] = chart_data_sex['p9_code'].map(sex_mapping)
            # Define una escala de colores para los sexos
            color_scale_sex = alt.Scale(domain=list(sex_mapping.values()), range=['#1f77b4', '#ff7f0e'])
            # Crea el gráfico de barras
            chart_sex = alt.Chart(chart_data_sex).mark_bar().encode(
                x=alt.X('Sexo', title='Sexo'), y=alt.Y('Count', title='Número de Participantes'),
                color=alt.Color('Sexo', scale=color_scale_sex, legend=None), tooltip=['Sexo', 'Count']
            ).properties(title='Distribución de Participantes por Sexo').interactive()
            st.altair_chart(chart_sex, use_container_width=True)
        else:
            st.warning("La columna de sexo ('p9') no se encontró en el archivo CSV para este análisis.")

        st.markdown("---")

        st.subheader('Distribución de Edades')
        st.write("Este histograma ilustra cómo se agrupan los participantes por rango de edad (columna P8R), dándonos una idea de la estructura etaria de la población encuestada.")
        # Verifica si la columna 'p8r' existe
        if 'p8r' in df.columns:
             # Asegurarse de que la columna de edad sea numérica, convirtiendo errores a NaN y eliminando NaNs
            df['p8r_numeric'] = pd.to_numeric(df['p8r'], errors='coerce')
            # Crea un histograma usando Altair
            chart_age = alt.Chart(df.dropna(subset=['p8r_numeric'])).mark_bar().encode( # Elimina filas con NaNs en la edad numérica para el gráfico
                x=alt.X('p8r_numeric', bin=alt.Bin(maxbins=20), title='Rango de Edades'), # Define bins para agrupar edades
                y=alt.Y('count()', title='Frecuencia'), # Cuenta la frecuencia en cada bin
                color=alt.Color('p8r_numeric', bin=alt.Bin(maxbins=20), scale=alt.Scale(scheme='pastel1'), title='Rango de Edades'), # Colorea por rango de edad
                tooltip=[alt.Tooltip('p8r_numeric', bin=True, title='Rango de Edades'), 'count()', alt.Tooltip('p8r_numeric', bin=True, title='Color representa Rango de Edad')] # Tooltip mejorado
            ).properties(title='Histograma de Edades de los Participantes').interactive()
            st.altair_chart(chart_age, use_container_width=True)
        else:
            st.warning("La columna de edad ('p8r') no se encontró en el archivo CSV para este análisis.")


    # --- Sección: Condiciones de Vida (P12 y P13) ---
    elif page_selection == "Condiciones de Vida":
        st.header('El Día a Día: ¿Dónde Duermen?')
        st.markdown("""
            Las condiciones de vida son un aspecto central de la realidad de los habitantes de calle.
            ¿Dónde encuentran refugio habitualmente? Estos gráficos muestran el tipo de lugar donde
            suelen dormir los participantes, revelando si es directamente en la calle, en dormitorios
            habilitados o en instituciones. Comprender estos patrones es vital para planificar servicios de refugio.
        """)

        st.subheader('¿En qué municipio duerme usted habitualmente?')
        st.write('Según la pregunta P12, ¿su lugar habitual para dormir está en el mismo municipio de la encuesta, en otro municipio o incluso en otro país?')
        # Verifica si la columna 'p12' existe
        if 'p12' in df.columns:
            # Cuenta la frecuencia de cada código de lugar donde duerme
            p12_counts = df['p12'].value_counts().reset_index()
            p12_counts.columns = ['Code', 'Count']
            # Filtra códigos no esperados que no estén en el mapeo
            p12_counts = p12_counts[p12_counts['Code'].isin(p12_mapping.keys())]
            # Mapea códigos a etiquetas
            p12_counts['Lugar'] = p12_counts['Code'].map(p12_mapping)
            # Crea el gráfico de barras
            chart_p12 = alt.Chart(p12_counts).mark_bar().encode(
                x=alt.X('Lugar', title='Lugar donde duerme'), y=alt.Y('Count', title='Frecuencia'),
                color=alt.Color('Lugar', legend=None), tooltip=['Lugar', 'Count']
            ).properties(title='Distribución: Lugar donde duerme habitualmente').interactive()
            st.altair_chart(chart_p12, use_container_width=True)
        else:
             st.warning("La columna 'p12' (Municipio donde duerme) no se encontró en el archivo CSV para este análisis.")

        st.markdown("---")

        st.subheader('¿Dónde duerme usted habitualmente?')
        st.write('La pregunta P13 indaga específicamente sobre el tipo de lugar: la calle, un dormitorio o una institución. Este gráfico muestra la prevalencia de cada uno, destacando la proporción que duerme directamente en la calle.')
        # Verifica si la columna 'p13' existe
        if 'p13' in df.columns:
            # Cuenta la frecuencia de cada código de tipo de lugar
            p13_counts = df['p13'].value_counts().reset_index()
            p13_counts.columns = ['Code', 'Count']
            # Filtra códigos no esperados que no estén en el mapeo
            p13_counts = p13_counts[p13_counts['Code'].isin(p13_mapping.keys())]
            # Mapea códigos a etiquetas
            p13_counts['Lugar'] = p13_counts['Code'].map(p13_mapping)
            # Crea el gráfico de barras
            chart_p13 = alt.Chart(p13_counts).mark_bar().encode(
                 x=alt.X('Lugar', title='Tipo de lugar donde duerme'), y=alt.Y('Count', title='Frecuencia'),
                color=alt.Color('Lugar', legend=None), tooltip=['Lugar', 'Count']
            ).properties(title='Distribución: Tipo de lugar donde duerme habitualmente').interactive()
            st.altair_chart(chart_p13, use_container_width=True)
        else:
             st.warning("La columna 'p13' (Tipo de lugar donde duerme) no se encontró en el archivo CSV para este análisis.")


    # --- Sección: Salud y Discapacidad (P16 y P20) ---
    elif page_selection == "Salud y Discapacidad":
        st.header('Bienestar y Desafíos de Salud')
        st.markdown("""
            La salud es una dimensión crítica de la vida, especialmente en contextos de alta vulnerabilidad.
            Esta sección explora las capacidades sensoriales (oír, hablar) y la prevalencia de diagnósticos
            de ciertas enfermedades entre los participantes, ofreciendo una perspectiva sobre los desafíos
            de salud que enfrentan los habitantes de calle encuestados.
        """)

        st.subheader('Capacidades Sensoriales y de Comunicación')
        st.write("Las preguntas P16S1 y P16S2 exploran la capacidad de oír y hablar. Las dificultades en estas áreas pueden representar barreras significativas para la interacción, el acceso a ayuda y la seguridad personal.")

        st.write('**¿Puede oír la voz o los sonidos? (P16S1)**')
        st.write('1 = No puede, 2 = Mucha dificultad, 3 = Con dificultad, 4 = Sin esfuerzo')
        # Verifica si la columna 'p16s1' existe
        if 'p16s1' in df.columns:
            # Cuenta la frecuencia de cada nivel de capacidad
            p16s1_counts = df['p16s1'].value_counts().reset_index()
            p16s1_counts.columns = ['Code', 'Count']
             # Filtra códigos no esperados que no estén en el mapeo
            p16s1_counts = p16s1_counts[p16s1_counts['Code'].isin(p16_mapping.keys())]
            # Mapea códigos a etiquetas
            p16s1_counts['Capacidad'] = p16s1_counts['Code'].map(p16_mapping)
            # Crea el gráfico de barras, ordenando por el orden lógico de las capacidades
            chart_p16s1 = alt.Chart(p16s1_counts).mark_bar().encode(
                x=alt.X('Capacidad', sort=list(p16_mapping.values()), title='Nivel de Capacidad'), # Ordena según el mapeo
                y=alt.Y('Count', title='Frecuencia'), color=alt.Color('Capacidad', legend=None), tooltip=['Capacidad', 'Count']
            ).properties(title='Capacidad de Oír').interactive()
            st.altair_chart(chart_p16s1, use_container_width=True)
        else:
             st.warning("La columna 'p16s1' (Capacidad de oír) no se encontró en el archivo CSV para este análisis.")


        st.markdown("---")

        st.write('**¿Puede hablar o conversar? (P16S2)**')
        st.write('1 = No puede, 2 = Mucha dificultad, 3 = Con dificultad, 4 = Sin esfuerzo')
        # Verifica si la columna 'p16s2' existe
        if 'p16s2' in df.columns:
            # Cuenta la frecuencia de cada nivel de capacidad
            p16s2_counts = df['p16s2'].value_counts().reset_index()
            p16s2_counts.columns = ['Code', 'Count']
            # Filtra códigos no esperados que no estén en el mapeo
            p16s2_counts = p16s2_counts[p16s2_counts['Code'].isin(p16_mapping.keys())]
            # Mapea códigos a etiquetas
            p16s2_counts['Capacidad'] = p16s2_counts['Code'].map(p16_mapping)
            # Crea el gráfico de barras, ordenando por el orden lógico de las capacidades
            chart_p16s2 = alt.Chart(p16s2_counts).mark_bar().encode(
                 x=alt.X('Capacidad', sort=list(p16_mapping.values()), title='Nivel de Capacidad'),
                y=alt.Y('Count', title='Frecuencia'), color=alt.Color('Capacidad', legend=None), tooltip=['Capacidad', 'Count']
            ).properties(title='Capacidad de Hablar').interactive()
            st.altair_chart(chart_p16s2, use_container_width=True)
        else:
             st.warning("La columna 'p16s2' (Capacidad de hablar) no se encontró en el archivo CSV para este análisis.")

        st.markdown("---")

        st.subheader("Diagnóstico de Enfermedades Reportadas (P20)")
        st.markdown("""
            Más allá de las capacidades sensoriales, la presencia de enfermedades crónicas o graves es una preocupación importante para la salud pública en esta población.
            Este cuadro resume la frecuencia y el porcentaje de participantes que reportaron haber sido diagnosticados con
            condiciones como Hipertensión, Diabetes, Cáncer, Tuberculosis y VIH-SIDA (preguntas P20S1 a P20S5).
        """)
        # Identifica las columnas de enfermedades que existen en el dataframe
        health_cols_present = [col for col in p20_preguntas.keys() if col in df.columns]
        if health_cols_present:
            st.write("**Frecuencia de Diagnósticos**")
            resumen = {'Enfermedad': [], 'Sí': [], 'No': []}
            # Itera sobre las columnas de enfermedades presentes
            for col in health_cols_present:
                enfermedad = p20_preguntas[col] # Obtiene la etiqueta de la enfermedad
                conteo = df[col].value_counts() # Cuenta la frecuencia de respuestas (1=Sí, 2=No)
                si = conteo.get(1, 0) # Obtiene el conteo para 'Sí', 0 si no existe
                no = conteo.get(2, 0) # Obtiene el conteo para 'No', 0 si no existe
                resumen['Enfermedad'].append(enfermedad)
                resumen['Sí'].append(si)
                resumen['No'].append(no)
            df_resumen = pd.DataFrame(resumen)
            st.dataframe(df_resumen)

            st.write("**Porcentaje de Diagnósticos**")
            total = df_resumen['Sí'] + df_resumen['No']
            # Evita la división por cero si una columna de enfermedad tiene solo NaNs u otros códigos
            total = total.replace(0, np.nan)
            df_porcentajes = pd.DataFrame({
                'Enfermedad': df_resumen['Enfermedad'],
                'Sí (%)': (df_resumen['Sí'] / total * 100).round(2).fillna(0), # Calcula porcentaje de 'Sí', rellena NaN con 0
                'No (%)': (df_resumen['No'] / total * 100).round(2).fillna(0) # Calcula porcentaje de 'No', rellena NaN con 0
            })
            st.dataframe(df_porcentajes)
        else:
            st.warning("Ninguna de las columnas de diagnóstico de enfermedades (P20S1 a P20S5) se encontró en el archivo CSV para este análisis.")


    # --- Sección: Razones y Tiempo Viviendo en la Calle (P22 y P23S1R) ---
    elif page_selection == "Razones y Tiempo en Calle":
        st.header("El Camino a la Calle: Razones y Permanencia")
        st.markdown("""
            ¿Qué lleva a una persona a vivir en la calle? Las causas son múltiples y a menudo entrelazadas.
            Esta sección explora las principales razones reportadas por los participantes para encontrarse
            en esta situación, así como el tiempo que llevan viviendo en la calle. Comprender estos factores
            es crucial para diseñar programas de prevención y atención.
        """)

        st.subheader("Distribución de Razones Principales para Vivir en la Calle (P22)")
        st.markdown("""
            La pregunta P22 indaga sobre el factor principal que motivó o contribuyó a la situación de calle.
            Este gráfico muestra la frecuencia con la que se reporta cada una de las diversas razones,
            desde consumo de sustancias hasta conflictos familiares o falta de trabajo.
            Puedes usar el filtro para enfocarte en razones específicas y ver su prevalencia.
        """)
        # Verifica si la columna 'p22' existe
        if 'p22' in df.columns:
            # Obtiene las etiquetas de las razones para el multiselect
            opciones_mapa_p22 = list(p22_etiquetas.values())
            # Permite al usuario seleccionar razones para filtrar
            opciones_seleccionadas_p22 = st.multiselect(
                "Selecciona las razones a mostrar",
                opciones_mapa_p22, default=opciones_mapa_p22, key='filter_p22' # Por defecto, muestra todas
            )

            # Cuenta la frecuencia de cada código de razón
            data_p22 = df['p22'].value_counts().sort_index()

            # Procede solo si hay opciones seleccionadas (o si se muestran todas por defecto)
            if opciones_seleccionadas_p22:
                # Mapear las etiquetas seleccionadas de vuelta a los códigos numéricos
                selected_p22_codes = [code for code, label in p22_etiquetas.items() if label in opciones_seleccionadas_p22]
                # Filtra los datos para incluir solo los códigos seleccionados
                data_p22_filtrada = data_p22[data_p22.index.isin(selected_p22_codes)]

                # Verifica si hay datos después de filtrar
                if not data_p22_filtrada.empty:
                    fig_p22, ax_p22 = plt.subplots(figsize=(12, 7)) # Aumenta el tamaño de la figura
                    # Crea el gráfico de barras con un mapa de colores
                    bars = ax_p22.bar(data_p22_filtrada.index, data_p22_filtrada.values, color=plt.cm.Paired(np.arange(len(data_p22_filtrada)))) # Usa un mapa de colores
                    ax_p22.set_xticks(data_p22_filtrada.index)
                    # Usa etiquetas del mapeo para los ticks del eje X
                    ax_p22.set_xticklabels([p22_etiquetas.get(i, f"Code {i}") for i in data_p22_filtrada.index], rotation=45, ha='right')
                    ax_p22.set_xlabel("Razones")
                    ax_p22.set_ylabel("Frecuencia")
                    ax_p22.set_title("Distribución Filtrada de Razones Principales para Vivir en la Calle")
                    plt.tight_layout() # Ajusta el layout para evitar solapamiento
                    st.pyplot(fig_p22) # Muestra el gráfico
                else:
                     st.info("No hay datos disponibles para las razones seleccionadas en el conjunto de datos.")
            elif not data_p22.empty: # Muestra todas si no se seleccionaron opciones inicialmente y hay datos
                fig_p22, ax_p22 = plt.subplots(figsize=(12, 7)) # Aumenta el tamaño de la figura
                bars = ax_p22.bar(data_p22.index, data_p22.values, color=plt.cm.Paired(np.arange(len(data_p22)))) # Usa un mapa de colores
                 # Usa solo los códigos que existen en los datos para los ticks del eje X
                existing_p22_codes = data_p22.index.tolist()
                ax_p22.set_xticks(existing_p22_codes)
                ax_p22.set_xticklabels([p22_etiquetas.get(i, f"Code {i}") for i in existing_p22_codes], rotation=45, ha='right')
                ax_p22.set_xlabel("Razones")
                ax_p22.set_ylabel("Frecuencia")
                ax_p22.set_title("Distribución Completa de Razones Principales para Vivir en la Calle")
                plt.tight_layout()
                st.pyplot(fig_p22)
            else:
                 st.info("No hay datos disponibles para las razones principales para vivir en la calle ('p22').")
        else:
            st.warning("La columna 'p22' (Razones para vivir en la calle) no se encontró en el archivo CSV para este análisis.")

        st.markdown("---")

        st.subheader("Tiempo Viviendo en la Calle (P23S1R)")
        st.markdown("""
            El tiempo que una persona lleva viviendo en la calle es un indicador importante de la cronicidad de su situación.
            Esta sección presenta estadísticas descriptivas y una visualización de la distribución de este tiempo reportado
            en años (columna P23S1R).
            Utiliza el control deslizante para explorar la distribución dentro de rangos de tiempo específicos y observar cómo varía la frecuencia.
        """)
        # Verifica si la columna 'p23s1r' existe
        if 'p23s1r' in df.columns:
            # Convierte la columna a numérica, maneja errores como NaN y elimina NaNs
            data_p23 = pd.to_numeric(df['p23s1r'], errors='coerce').dropna()
            # Procede solo si hay datos válidos
            if not data_p23.empty:
                st.write("### Estadísticas Básicas del Tiempo en Calle")
                # Muestra estadísticas clave usando columnas de Streamlit
                col1, col2, col3 = st.columns(3)
                col1.metric("Promedio", f"{data_p23.mean():.1f} años")
                col2.metric("Mediana", f"{data_p23.median():.1f} años")
                col3.metric("Máximo", f"{int(data_p23.max())} años")

                st.write("### Distribución del Tiempo en la Calle")
                # Crea un histograma de la distribución completa
                fig_p23_hist, ax_p23_hist = plt.subplots(figsize=(10, 6))
                # Ajusta el número de bins dinámicamente, mínimo 10 si es posible
                bins_hist = min(50, int(data_p23.max()) if data_p23.max() > 0 else 10) if data_p23.max() > 0 else 10
                sns.histplot(data_p23, bins=bins_hist, kde=True, color='skyblue', ax=ax_p23_hist) # Añade una curva de densidad (kde)
                ax_p23_hist.set_xlabel("Años Viviendo en la Calle")
                ax_p23_hist.set_ylabel("Frecuencia")
                ax_p23_hist.set_title("Distribución del Tiempo Viviendo en la Calle")
                plt.tight_layout()
                st.pyplot(fig_p23_hist)

                st.write("### Filtrar por Rango de Años")
                # Define el rango mínimo y máximo para el slider
                min_val = int(data_p23.min()) if data_p23.min() >= 0 else 0 # Asegura que el mínimo no sea negativo
                max_val = int(data_p23.max()) if data_p23.max() >= 0 else 1 # Asegura que el máximo sea al menos 1
                if min_val > max_val: min_val, max_val = max_val, min_val # Asegura que min <= max
                if min_val == max_val and max_val > 0: max_val +=1 # Asegura un rango si todos los valores son el mismo número positivo

                # Crea un slider para seleccionar el rango de años
                min_anos, max_anos = st.slider("Selecciona el rango de años",
                                               min_val, max_val,
                                               (min_val, max_val), key='filter_p23')

                # Filtra los datos según el rango seleccionado por el usuario
                data_p23_filtrada = data_p23[(data_p23 >= min_anos) & (data_p23 <= max_anos)]

                # Muestra el histograma filtrado si hay datos en el rango
                if not data_p23_filtrada.empty:
                    fig_p23_filtered, ax_p23_filtered = plt.subplots(figsize=(10, 6))
                    # Ajusta los bins para los datos filtrados, asegurando al menos 5 bins si es posible
                    bins_filtered = max(5, int(len(data_p23_filtrada)/10) if len(data_p23_filtrada)/10 > 5 else len(data_p23_filtrada) // 2 if len(data_p23_filtrada) > 0 else 1)
                    if data_p23_filtrada.nunique() > 1: # Usa histplot solo si hay variación en los datos filtrados
                        sns.histplot(data_p23_filtrada, bins=bins_filtered, kde=True, color='lightcoral', ax=ax_p23_filtered)
                        ax_p23_filtered.set_xlabel("Años Viviendo en la Calle (Filtrado)")
                        ax_p23_filtered.set_ylabel("Frecuencia")
                        ax_p23_filtered.set_title(f"Distribución (Rango: {min_anos} - {max_anos} años)")
                        plt.tight_layout()
                        st.pyplot(fig_p23_filtered)
                    else:
                         st.info(f"Todos los datos en el rango seleccionado ({min_anos} - {max_anos} años) tienen el mismo valor. No se puede mostrar un histograma de distribución.")
                         if not data_p23_filtrada.empty:
                            st.write(f"Valor único en este rango: {data_p23_filtrada.iloc[0]} años.")
                else:
                     st.info("No hay datos disponibles para el rango de años seleccionado.")

                st.write("### Observaciones Clave")
                # Proporciona observaciones basadas en las estadísticas calculadas
                st.write(f"- En promedio, los participantes reportan llevar aproximadamente **{data_p23.mean():.1f} años** viviendo en la calle.")
                if not data_p23.mode().empty:
                   st.write(f"- El tiempo más frecuentemente reportado (moda) es de **{data_p23.mode()[0]} años**.")
                st.write(f"- La experiencia de vivir en la calle puede ser de muy larga duración para algunos, con individuos reportando hasta **{int(data_p23.max())} años**.")

            else:
                st.warning("No hay datos válidos para el análisis de tiempo viviendo en la calle (P23S1R).")
        else:
            st.warning("La columna 'p23s1r' (Tiempo viviendo en la calle) no se encontró en el archivo CSV para este análisis.")


    # --- Sección: Fuentes de Ayuda (P26_1) ---
    elif page_selection == "Fuentes de Ayuda":
        st.header("Redes de Apoyo: ¿Quién Ayuda?")
        st.markdown("""
            Enfrentar la vida en la calle es un desafío inmenso. Las redes de apoyo, ya sean formales (instituciones) o informales (familia, amigos),
            juegan un papel vital en la supervivencia y la posibilidad de salir de esta situación. Esta sección explora cuál es la principal fuente de ayuda que reportan
            recibir los participantes de la encuesta (columna P26_1).
            Conocer estas fuentes puede informar sobre dónde enfocar esfuerzos de intervención y fortalecer los apoyos existentes.
        """)
        st.subheader("Principal Fuente de Ayuda (P26_1)")
        st.write("Este gráfico de pastel muestra la proporción de participantes según de quién proviene la principal fuente de ayuda que reciben, ofreciendo una visión general de las redes de apoyo más comunes.")
        st.write("*Opciones reportadas: 1 = Familiar, 2 = Amigos, 3 = Instituciones oficiales, 4 = Instituciones/organizaciones privadas, 5 = Organizaciones religiosas, 6 = Otros.*")

        # Verifica si la columna 'p26_1' existe
        if 'p26_1' in df.columns:
            # Cuenta la frecuencia de cada código de fuente de ayuda
            data_p26 = df['p26_1'].value_counts().sort_index()
            # Filtra códigos no esperados que no estén en el mapeo
            data_p26 = data_p26[data_p26.index.isin(p26_etiquetas.keys())]

            # Muestra el gráfico de pastel general si hay datos
            if not data_p26.empty:
                st.write("### Distribución General de la Principal Fuente de Ayuda")
                fig_p26, ax_p26 = plt.subplots(figsize=(8, 8))
                # Usa el índice de los datos para mapear a etiquetas
                labels_p26 = [p26_etiquetas.get(i, f"Code {i}") for i in data_p26.index]
                ax_p26.pie(data_p26.values, labels=labels_p26, autopct='%1.1f%%', startangle=90, wedgeprops=dict(width=0.3))
                ax_p26.axis('equal') # Asegura que el pastel sea un círculo
                ax_p26.set_title("Distribución de la Principal Fuente de Ayuda")
                st.pyplot(fig_p26)
            else:
                 st.info("No hay datos disponibles válidos para la fuente de ayuda principal ('p26_1').")

            st.write("### Filtrar Fuentes de Ayuda")
            # Obtiene las etiquetas de las fuentes de ayuda para el multiselect
            opciones_mapa_p26 = list(p26_etiquetas.values())
            # Permite al usuario seleccionar fuentes para filtrar el gráfico
            opciones_seleccionadas_p26 = st.multiselect(
                "Selecciona las fuentes a mostrar en el gráfico filtrado",
                opciones_mapa_p26, default=[], key='filter_p26' # Por defecto, no muestra nada en el gráfico filtrado hasta que se selecciona
            )
            # Muestra el gráfico filtrado si hay opciones seleccionadas
            if opciones_seleccionadas_p26:
                # Mapear etiquetas seleccionadas de vuelta a códigos
                indices_p26 = [code for code, label in p26_etiquetas.items() if label in opciones_seleccionadas_p26]
                # Filtra los datos para incluir solo los códigos seleccionados
                data_p26_filtrada = data_p26[data_p26.index.isin(indices_p26)]
                # Muestra el gráfico filtrado si hay datos
                if not data_p26_filtrada.empty:
                    fig_p26_filtered, ax_p26_filtered = plt.subplots(figsize=(8, 8))
                    labels_p26_filtered = [p26_etiquetas.get(i, f"Code {i}") for i in data_p26_filtrada.index]
                    ax_p26_filtered.pie(data_p26_filtrada.values, labels=labels_p26_filtered, autopct='%1.1f%%', startangle=90, wedgeprops=dict(width=0.3))
                    ax_p26_filtered.axis('equal')
                    ax_p26_filtered.set_title("Distribución Filtrada de la Principal Fuente de Ayuda")
                    st.pyplot(fig_p26_filtered)
                else:
                     st.info("No hay datos para las fuentes de ayuda seleccionadas en el conjunto de datos.")
            # No se necesita un else aquí, ya que el comportamiento por defecto es no mostrar el gráfico filtrado si no hay selección.
        else:
            st.warning("La columna 'p26_1' (Principal fuente de ayuda) no se encontró en el archivo CSV para este análisis.")


    # --- Sección: Análisis de Consumo Actual de Sustancias (P30S) ---
    # Se omite la parte de Edad Promedio de Inicio del Consumo por Sustancia según la solicitud del usuario.
    elif page_selection == "Consumo de Sustancias":
        st.header("El Consumo de Sustancias: Prevalencia")
        st.markdown("""
            El consumo de sustancias psicoactivas es un factor complejo y a menudo asociado con la situación de calle.
            Esta sección presenta datos sobre la prevalencia del consumo actual de diferentes sustancias,
            según lo reportado por los participantes en la encuesta CHC_2021.
            Comprender estos patrones es fundamental para diseñar programas de salud y reducción de daños efectivos.
        """)

        # --- Datos Reales para el Porcentaje de Consumo de Sustancias (P30S) ---
        st.subheader("Porcentaje de Personas que Consumen Cada Sustancia (Actual)")
        st.write("Este gráfico de barras horizontales muestra el porcentaje de participantes que reportaron consumir actualmente cada una de las sustancias listadas (columnas P30S1 a P30S9, respuesta '1'). Los porcentajes se calculan sobre el total de participantes en la encuesta.")

        substance_data_current = []
        # Considera el total de filas en el dataframe para el denominador del porcentaje
        total_respondents = df.shape[0]

        if total_respondents > 0:
            # Identifica las columnas de consumo actual que existen en el dataframe
            existing_substance_cols_current = [col for col in substance_cols_mapping_current.keys() if col in df.columns]
            if existing_substance_cols_current:
                # Itera sobre el mapeo de columnas de consumo actual
                for col_code, substance_name in substance_cols_mapping_current.items():
                    # Procede solo si la columna existe en el dataframe
                    if col_code in df.columns:
                        # Cuenta cuántos respondieron '1' (Sí) para esta sustancia
                        yes_count = df[col_code].value_counts().get(1, 0)
                        # Calcula el porcentaje sobre el total de participantes
                        percentage = (yes_count / total_respondents) * 100
                        substance_data_current.append({"Sustancia": substance_name, "Porcentaje": percentage})
                    else:
                         st.warning(f"Columna '{col_code}' no encontrada en el archivo CSV. No se puede incluir en el análisis de consumo actual.")
                         substance_data_current.append({"Sustancia": substance_name, "Porcentaje": 0}) # Añade con 0% si la columna no existe


                # Muestra el gráfico si se recopiló información de al menos una sustancia
                if substance_data_current:
                    df_sustancias_current = pd.DataFrame(substance_data_current)
                    # Ordena por porcentaje descendente para mejor visualización
                    df_sustancias_current = df_sustancias_current.sort_values("Porcentaje", ascending=False)

                    # Crea el gráfico de barras con Plotly Express
                    fig_sustancias_current = px.bar(
                        df_sustancias_current, x="Porcentaje", y="Sustancia", orientation="h", # Barras horizontales
                        title="Porcentaje de Participantes que Consumen Cada Sustancia (Actual)",
                        color="Sustancia", text="Porcentaje", # Colorea por sustancia y muestra el porcentaje como texto
                    )
                    fig_sustancias_current.update_traces(texttemplate="%{text:.1f}%", textposition="outside") # Formato del texto
                    fig_sustancias_current.update_layout(
                        xaxis_title="Porcentaje de Participantes (%)", yaxis_title="Sustancia", showlegend=False, height=500, xaxis_range=[0, 100] # Ajusta layout
                    )
                    st.plotly_chart(fig_sustancias_current) # Muestra el gráfico
                else:
                    st.info("No hay datos disponibles para calcular el consumo actual de sustancias de las columnas P30S.")
            else:
                st.warning("Ninguna de las columnas de consumo actual de sustancias (P30S1-P30S9) se encontró en el archivo CSV.")
        else:
            st.info("No hay datos en el DataFrame para analizar el consumo actual de sustancias.")

        # --- Se omite la sección de Edad Promedio de Inicio del Consumo por Sustancia ---


    # --- Sección: Seguridad en la Calle (P33S) ---
    elif page_selection == "Seguridad en la Calle":
        st.header("Vivir en Riesgo: Factores de Seguridad en la Calle")
        st.markdown("""
            La seguridad es una preocupación constante y un desafío fundamental para las personas que viven en la calle.
            Están expuestas a diversos riesgos. Esta sección analiza los factores específicos que los participantes reportan
            que han afectado su seguridad, como persecución por grupos, abuso policial o problemas
            con la comunidad (basado en las columnas P33S1 a P33S6).
            Comprender estos riesgos es fundamental para diseñar estrategias de protección y entornos más seguros.
        """)

        st.subheader("Factores que Afectan la Seguridad en la Calle")
        st.write("Este gráfico muestra el porcentaje de participantes que reportaron que su seguridad se vio afectada por cada uno de los factores listados (respuesta '1' = Sí). Los porcentajes se calculan sobre el total de participantes que respondieron a la pregunta específica.")

        security_data = []
        total_respondents = df.shape[0]

        if total_respondents > 0:
            # Identifica las columnas de seguridad que existen en el dataframe
            existing_security_cols = [col for col in security_factors_mapping.keys() if col in df.columns]
            if existing_security_cols:
                # Itera sobre el mapeo de factores de seguridad
                for col_code, factor_description in security_factors_mapping.items():
                    # Procede solo si la columna existe en el dataframe
                    if col_code in df.columns:
                        # Considera solo valores no NaN para el denominador para un porcentaje más preciso por factor
                        valid_counts = df[col_code].dropna().shape[0]
                        if valid_counts > 0:
                             yes_count = df[col_code].value_counts().get(1, 0) # Cuenta cuántos respondieron '1' (Sí)
                             percentage = (yes_count / valid_counts) * 100 # Calcula el porcentaje sobre las respuestas válidas
                             security_data.append({"Factor de Seguridad": factor_description, "Porcentaje": percentage})
                        else:
                            security_data.append({"Factor de Seguridad": factor_description, "Porcentaje": 0}) # Añade con 0% si no hay respuestas válidas
                    else:
                        st.warning(f"Columna '{col_code}' no encontrada en el archivo CSV. No se puede incluir en el análisis de seguridad.")
                        security_data.append({"Factor de Seguridad": factor_description, "Porcentaje": 0}) # Añade con 0% si la columna no existe

                # Muestra el gráfico si se recopiló información de al menos un factor
                if security_data:
                    df_security = pd.DataFrame(security_data)
                    # Ordena por porcentaje descendente
                    df_security = df_security.sort_values("Porcentaje", ascending=False)

                    # Crea el gráfico de barras con Plotly Express
                    fig_security = px.bar(
                        df_security, x="Porcentaje", y="Factor de Seguridad", orientation="h", # Barras horizontales
                        title="Porcentaje de Participantes Afectados por Factores de Seguridad en la Calle",
                        color="Factor de Seguridad", text="Porcentaje", # Colorea por factor y muestra el porcentaje
                    )
                    fig_security.update_traces(texttemplate="%{text:.1f}%", textposition="outside") # Formato del texto
                    fig_security.update_layout(
                        xaxis_title="Porcentaje de Participantes (%)", yaxis_title="Factor de Seguridad",
                        showlegend=False, height=400, xaxis_range=[0, 100] # Ajusta layout
                    )
                    st.plotly_chart(fig_security, use_container_width=True) # Muestra el gráfico

                else:
                    st.info("No hay datos disponibles para analizar los factores de seguridad de las columnas P33S.")
            else:
                 st.warning("Ninguna de las columnas de seguridad (P33S1-P33S6) se encontró en el archivo CSV.")
        else:
            st.info("No hay datos en el DataFrame para analizar los factores de seguridad.")


    # --- Nueva Sección: Indicador de Vulnerabilidad ---
    elif page_selection == "Indicador de Vulnerabilidad":
        st.header("Indicador de Vulnerabilidad Multifactorial: Una Mirada Integral")

        st.markdown("""
            ### Comprendiendo la Vulnerabilidad Acumulada

            La situación de calle no es un problema único; a menudo, las personas enfrentan una
            combinación compleja de desafíos interrelacionados en diferentes áreas de sus vidas.
            Para capturar esta complejidad y ofrecer una visión más holística,
            hemos construido un indicador de vulnerabilidad multifactorial basado en los datos de la encuesta.

            **¿Cómo funciona el Indicador?**

            Este indicador asigna un punto por cada *tipo principal* de desafío o condición de vulnerabilidad
            que el participante reportó enfrentar, sumando hasta un máximo de 5 puntos.
            Un puntaje más alto sugiere que la persona acumula un mayor número de estas adversidades
            simultáneamente, lo que podría implicar una mayor necesidad de apoyo integral y coordinado.

            **Los 5 Componentes Clave Considerados:**

            1.  **Alguna Enfermedad:** Reportar tener al menos una de las enfermedades listadas (Hipertensión, Diabetes, Cáncer, Tuberculosis, VIH-SIDA) (basado en P20S1-P20S5).
            2.  **Alguna Discapacidad Sensorial/Comunicativa:** Reportar dificultad significativa o imposibilidad para oír (P16S1) o hablar (P16S2).
            3.  **Consumo Actual de Sustancias:** Reportar consumir actualmente al menos una sustancia psicoactiva de la lista (basado en P30S1-P30S9).
            4.  **Seguridad Afectada:** Reportar que la seguridad personal en la calle ha sido comprometida por algún factor (persecución, abuso policial, problemas con grupos, etc.) (basado en P33S1-P33S6).
            5.  **Duerme en la Calle:** Reportar que el lugar habitual para dormir es directamente la calle (basado en P13).

            **Interpretación del Puntaje:**
            -   **Puntaje de 0:** El participante no reportó ninguna de las 5 categorías de vulnerabilidad específicas consideradas por el indicador.
            -   **Puntaje de 5:** El participante reportó al menos un factor o condición en cada una de las 5 categorías de vulnerabilidad.

            El gráfico a continuación muestra cuántos participantes se encuentran en cada nivel de puntaje de vulnerabilidad (de 0 a 5),
            revelando la distribución de la carga de estas adversidades en la población encuestada y permitiendo identificar qué proporción enfrenta múltiples desafíos.
            """)

        st.subheader("Distribución del Puntaje de Vulnerabilidad Multifactorial")

        # Verifica si el DataFrame vulnerability_counts fue creado exitosamente y no está vacío
        if 'vulnerability_counts' in locals() and not vulnerability_counts.empty:

            # Crea el gráfico de barras de Altair para la distribución del puntaje de vulnerabilidad
            chart_vulnerability = alt.Chart(vulnerability_counts).mark_bar().encode(
                x=alt.X('Score:O', title='Puntaje de Vulnerabilidad (0-5)', sort='x'), # Usa tipo ordinal para asegurar el orden 0, 1, 2...
                y=alt.Y('Frequency', title='Número de Participantes'),
                tooltip=['Score', 'Frequency'] # Muestra puntaje y frecuencia al pasar el mouse
            ).properties(
                title='Distribución del Indicador de Vulnerabilidad Multifactorial'
            )

            # Añade etiquetas de texto encima de las barras para mostrar la frecuencia
            text = chart_vulnerability.mark_text(
                align='center',
                baseline='bottom',
                dy=-8 # Mueve el texto ligeramente hacia arriba
            ).encode(
                text='Frequency' # El texto a mostrar es la frecuencia
            )

            # Combina el gráfico de barras y las etiquetas de texto
            final_chart_vulnerability = chart_vulnerability + text

            st.altair_chart(final_chart_vulnerability, use_container_width=True) # Muestra el gráfico combinado

            st.markdown("""
                **Análisis de la Distribución:**

                Observa qué puntajes de vulnerabilidad son más frecuentes en la población encuestada.
                Un pico en puntajes bajos podría indicar que una
                parte significativa de la población, aunque en situación de calle, no reporta estos
                factores de vulnerabilidad específicos considerados por el indicador.
                Por otro lado, un pico o una distribución amplia en puntajes más altos sugiere que muchas personas enfrentan múltiples y severos desafíos simultáneamente.
                Esta información es vital para entender la heterogeneidad de la población habitante de calle
                y orientar intervenciones más complejas e integrales para quienes acumulan mayores vulnerabilidades,
                buscando abordar los múltiples factores que contribuyen a su situación.
            """)


        elif not df.empty: # Si el DataFrame se cargó pero el cálculo del indicador falló o resultó en conteos vacíos
             st.warning("No se pudieron calcular los puntajes de vulnerabilidad. Verifica que las columnas utilizadas en el cálculo existan y contengan datos válidos ('p20s1-p20s5', 'p16s1', 'p16s2', 'p30s1-p30s9', 'p33s1-p33s6', 'p13').")

        else: # Si el DataFrame inicial no fue cargado
             st.error("El DataFrame no fue cargado, por lo tanto, no se puede calcular ni mostrar el indicador de vulnerabilidad.")


# --- Maneja el caso en que el DataFrame esté vacío (ej. archivo no encontrado) ---
else:
    # Este mensaje ya se muestra por la función load_data, pero repetirlo aquí
    # asegura que el usuario sepa por qué el resto de la página está vacío.
    st.error("No se pudo cargar el archivo de datos inicial. Por favor, verifica la ruta y el formato del archivo.")

