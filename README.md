# Scraper  
Descarga la información del calendario de dias hábiles oficial del poder judicial de Córdoba y otorga un objeto conteniendo un objeto por cada mes del año (por ahora sólo del 2021), y éste objeto "mes" tiene a su vez un objeto "día" por cada día de la semana (excluye fines de semana). Cada dia tiene una propiedad "inhabil", y, si esta es verdadera, una propiedad "razón" con la razón de porque el día es inhábil. 