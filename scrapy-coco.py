# for scrapping 
import time
from datetime import date
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
import pandas as pd
import json

# for database
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

class Day(Base):
    __tablename__= "days"
    
    mes = Column('mes', Integer)
    dia = Column('dia', Integer)
    inhabil = Column('inhabil', Boolean)
    razon = Column('razon', String(10000))
    created_at = Column('created_at', DateTime, default=date.today())
    id = Column('id', Integer, primary_key=True)


engine = create_engine('mysql://user:password!@localhost:3306/mysql', echo=True)
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)

session = Session()


# Setting up webdriver

path = "./chromedriver/chromedriver"
chrome_options = Options()
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--headless")

driver = webdriver.Chrome(path, options=chrome_options)
driver.get("https://www.justiciacordoba.gob.ar/justiciacordoba/servicios/DiasInhabiles.aspx")

# Scraping
# Trabajando la lista de meses y el boton de buscar
meses_dd = Select(driver.find_element_by_xpath('.//*[@id="ddlMeses"]'))
buscar_btn = driver.find_element_by_xpath('.//*[@id="btnBuscar"]')

lista_tabla_cruda = []
lista_tabla_limpia = []
lista_completa = []

# Iterando para ejecutar el scraping en todos los meses del año
for i in range(1,13):
    meses_dd.select_by_value(str(i))
    buscar_btn.click()

    time.sleep(1.5)

    # Obtener tabla de días hábiles e inhabiles en 2 objs. de selenium
    ## obtener tabla con razones de los feriados

    tabla_cruda = driver.find_element_by_xpath('.//*[@id="datepicker"]/div')
    inhabiles = tabla_cruda.find_elements_by_css_selector('[title=inhabil]')

    # Obtener PANDAS dataframe y eliminar sábados y domingos, TRASNFORMARLO EN LISTA UNIDIMENSIONAL SIN NESTED LISTS
    tabla_limpia = pd.read_html(driver.page_source)[0].drop('Sá', axis=1).drop('Do', axis=1).fillna(value=0).values.flatten().tolist()

    tabla_confinde = pd.read_html(driver.page_source)[0].fillna(value=0).values.flatten().tolist()
    lista_findes = []
    for j in tabla_confinde:
        if int(j) == 0:
            pass
        else:
            if j not in tabla_limpia:
                lista_findes.append(int(j))
                


    # Obtener Pandas dataframe con tabla de razones de los días inháblies, y transformarla en diccionario con fechas como keys y razones como values
    try: # xq si no se rompe en los meses sin feriados
        tabla_razones = pd.read_html(driver.page_source)[1].values.flatten().tolist()
        dict_razones = dict(zip(tabla_razones[::2], tabla_razones[1::2]))
        final_razones = []

        # este loop es para obtener solo el dd como key y el dd/mm/aaaa + razon como valor
        index = 0
        newdict = {}
        for key, value in dict_razones.items():
            newdict[int(key[:2])] = key + ' ' + value
            index += 1
        
        dict_razones = newdict
        
    except:
        pass

    # Transformo lista de str devuelta x pandas en ints. Remuevo acá los nan xq no sé usar el method dropna en el dataframe
    lista_dias_semana = []
    for j in tabla_limpia:
        if int(j) == 0:
            pass
        else:
            lista_dias_semana.append(int(j))
    #except:
        #pass
        

    lista_dias_inhabiles = []
    for index, dia in enumerate(inhabiles):

        if int(dia.text) not in lista_dias_semana:
            pass
        else:
            lista_dias_inhabiles.append(int(dia.text))

    lista_completa.append({
            "mes": i,
            "fines_de_semana": lista_findes,
            "dias_semana": lista_dias_semana,
            "dias_inhabiles": lista_dias_inhabiles,
            "razones": dict_razones
            }) 
    
# print(json.dumps(lista_completa))

# transformo al objeto final

final_list = []
session.execute('delete from days')
session.commit()
for month in lista_completa:

    for day in month["dias_semana"]:
        if day in month["dias_inhabiles"]:
            razon = month["razones"][day]

            db_day = Day(mes=month["mes"],dia=day ,inhabil=True, razon=razon)
        else:
            db_day = Day(mes=month["mes"],dia=day, inhabil=False)
        session.add(db_day)

session.commit()
session.close()
print("success")
driver.quit()



