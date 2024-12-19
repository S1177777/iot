from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import  HTTPException

import requests

import sqlite3
from fastapi.responses import JSONResponse

from pydantic import BaseModel



app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/")
def home():
    return {"message": "Welcome to the Eco-Home Management System"}



# 获取数据库连接
def get_db_connection():
    conn = sqlite3.connect('database2.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/api/logements")
def get_logements():
    """
     Retourner tous les logements et leurs données associées (pièces et capteurs)
    """
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Requêter les logements et les pièces
        c.execute('''
            SELECT 
                l.logement_id, 
                l.adresse, 
                p.piece_id, 
                p.piece_nom
            FROM 
                logement l
            LEFT JOIN 
                piece p ON l.logement_id = p.logement_id
            ORDER BY 
                l.logement_id, p.piece_id;
        ''')
        logements_data = c.fetchall()

        # Requêter les logements et les pièces
        c.execute('''
            SELECT 
                c.ca_id, 
                c.reference_commmerciale, 
                c.is_visible, 
                c.piece_id, 
                t.nom_type, 
                t.unite_mes
            FROM 
                capteuractionneur c
            LEFT JOIN 
                type t ON c.type_id = t.type_id;
        ''')
        capteurs_data = c.fetchall()

        conn.close()

        # Organiser les données
        logements = {}
        for row in logements_data:
            logement_id = row["logement_id"]
            if logement_id not in logements:
                logements[logement_id] = {
                    "adresse": row["adresse"],
                    "pieces": {}
                }
            if row["piece_id"]:
                logements[logement_id]["pieces"][row["piece_id"]] = {
                    "piece_nom": row["piece_nom"],
                    "capteurs": []
                }

        for capteur in capteurs_data:
            piece_id = capteur["piece_id"]
            for logement_id, logement_data in logements.items():
                if piece_id in logement_data["pieces"]:
                    logement_data["pieces"][piece_id]["capteurs"].append({
                        "ca_id": capteur["ca_id"],
                        "reference_commmerciale": capteur["reference_commmerciale"],
                        "is_visible": capteur["is_visible"],
                        "type": capteur["nom_type"],
                        "unit": capteur["unite_mes"]
                    })

        return JSONResponse(content=logements)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/api/consumption")
def get_consumption_data(logement_id: int = None):
    """
    按 logement_id 返回每个 logement 的 consumption 数据
    """
    conn = get_db_connection()
    c = conn.cursor()

    # Requêter les données de consommation
    query = '''
        SELECT 
            l.logement_id,
            l.adresse,
            p.piece_nom,
            t.nom_type,
            MAX(CAST(m.valeur AS FLOAT)) AS valeur,
            t.unite_mes
        FROM 
            logement l
        LEFT JOIN 
            piece p ON l.logement_id = p.logement_id
        LEFT JOIN 
            capteuractionneur c ON p.piece_id = c.piece_id
        LEFT JOIN 
            type t ON c.type_id = t.type_id
        LEFT JOIN 
            mesure m ON c.ca_id = m.ca_id
    '''
    if logement_id:
        query += " WHERE l.logement_id = ?"

    query += '''
        GROUP BY 
            l.logement_id, 
            p.piece_id, 
            t.nom_type
        ORDER BY 
            l.logement_id, p.piece_id;
    '''

    params = [logement_id] if logement_id else []
    c.execute(query, params)
    data = c.fetchall()

    # Structurer les données
    result = {}
    for row in data:
        logement_id = row["logement_id"]
        if logement_id not in result:
            result[logement_id] = {"adresse": row["adresse"], "pieces": {}}

        if row["piece_nom"]:
            piece_nom = row["piece_nom"]
            if piece_nom not in result[logement_id]["pieces"]:
                result[logement_id]["pieces"][piece_nom] = []

            result[logement_id]["pieces"][piece_nom].append({
                "type": row["nom_type"],
                "value": row["valeur"],
                "unit": row["unite_mes"]
            })

    conn.close()
    return JSONResponse(content=result)






@app.get("/api/sensors_status")
def get_sensors_status():
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Exécuter une requête pour obtenir les informations sur l'état des capteurs
        c.execute('''
            SELECT 
                c.ca_id,
                c.reference_commmerciale,
                c.port_communication,
                c.ca_type,
                p.piece_nom,
                t.nom_type,
                t.unite_mes,
                m.valeur,
                m.dateinsert
            FROM 
                capteuractionneur c
            JOIN 
                piece p ON c.piece_id = p.piece_id
            JOIN 
                type t ON c.type_id = t.type_id
            LEFT JOIN 
                mesure m ON c.ca_id = m.ca_id
            WHERE 
                c.is_visible = 1      
            ORDER BY 
                c.ca_id, m.dateinsert DESC;
        ''')
        sensors_data = c.fetchall()
        conn.close()

        # Convertir les résultats de la requête au format JSON
        return {"sensors": [dict(row) for row in sensors_data]}

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/api/savings")
def get_savings_data():
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Requêter la consommation électrique de chaque maison
        c.execute('''
            SELECT 
                l.logement_id,
                l.adresse,
                SUM(CAST(m.valeur AS FLOAT)) AS total_electric
            FROM 
                mesure m
            JOIN 
                capteuractionneur c ON m.ca_id = c.ca_id
            JOIN 
                type t ON c.type_id = t.type_id
            JOIN
                piece p ON c.piece_id = p.piece_id
            JOIN
                logement l ON p.logement_id = l.logement_id
            WHERE 
                t.nom_type = 'Électricité'
            GROUP BY 
                l.logement_id, l.adresse;
        ''')
        logements_electric_data = c.fetchall()

        # Requêter les données de facturation de chaque maison
        c.execute('''
            SELECT 
                l.logement_id,
                l.adresse,
                f.fac_date, 
                f.montant
            FROM 
                facture f
            JOIN
                logement l ON f.logement_id = l.logement_id
            WHERE 
                f.fac_type = 'Électricité'
            ORDER BY 
                l.logement_id, f.fac_date;
        ''')
        bills_data = c.fetchall()

        conn.close()

        # Structurer les données
        logements = {}
        for row in logements_electric_data:
            logement_id = row["logement_id"]
            logements[logement_id] = {
                "adresse": row["adresse"],
                "total_electric": row["total_electric"] or 0,
                "bills": []
            }

        for row in bills_data:
            logement_id = row["logement_id"]
            if logement_id in logements:
                logements[logement_id]["bills"].append({
                    "fac_date": row["fac_date"],
                    "montant": row["montant"]
                })

        # Retourner les données au format JSON
        return JSONResponse(content=logements)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)





#Écrire une route API qui retourne tous les capteurs et leur état actuel is_visible
@app.get("/api/sensors/configuration")
def get_sensors_configuration():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            SELECT 
                ca_id, reference_commmerciale, is_visible
            FROM 
                capteuractionneur;
        ''')
        sensors = c.fetchall()
        conn.close()

        return {"sensors": [dict(row) for row in sensors]}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    

from pydantic import BaseModel

class SensorVisibilityUpdate(BaseModel):
    ca_id: int
    is_visible: bool

# Créer une route API pour mettre à jour l'état is_visible d'un capteur spécifique
@app.put("/api/sensors/configuration")
def update_sensor_visibility(data: SensorVisibilityUpdate):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            UPDATE capteuractionneur
            SET is_visible = ?
            WHERE ca_id = ?;
        ''', (data.is_visible, data.ca_id))
        conn.commit()
        conn.close()

        return {"message": "Sensor visibility updated successfully"}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


#Créer une route API /api/sensors/types qui retourne les ca_id de tous les capteurs et leurs types correspondants (type_id)
@app.get("/api/sensors/types")
def get_sensor_types():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            SELECT 
                c.ca_id, c.reference_commmerciale, t.nom_type, t.unite_mes
            FROM 
                capteuractionneur c
            JOIN 
                type t ON c.type_id = t.type_id;
        ''')
        sensors = c.fetchall()
        conn.close()
        return {"sensors": [dict(row) for row in sensors]}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)



# Créer une route API /api/sensors/insert_measure pour insérer les valeurs saisies par l'utilisateur dans la table mesure
class InsertMeasure(BaseModel):
    ca_id: int
    valeur: str

@app.post("/api/sensors/insert_measure")
def insert_measure(data: InsertMeasure):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO mesure (ca_id, valeur, dateinsert)
            VALUES (?, ?, CURRENT_TIMESTAMP);
        ''', (data.ca_id, data.valeur))
        conn.commit()
        conn.close()
        return {"message": "Mesure insérée avec succès"}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


#sensor
class SensorData(BaseModel):
    temperature: float
    humidity: float

@app.post("/api/sensors/temperature")
async def receive_sensor_data(data: SensorData):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO temperature_data (temperature, humidity) VALUES (?, ?)",
            (data.temperature, data.humidity)
        )
        conn.commit()
        conn.close()
        return {"message": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sensors/temperature")
async def get_sensor_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM temperature_data ORDER BY timestamp DESC LIMIT 50")
    data = cursor.fetchall()
    conn.close()
    return [dict(row) for row in data]


# Configurer la clé API et l'URL de base (en utilisant WeatherAPI)
API_KEY = '15fd613ef60f4c1fbfe101051241511'
BASE_URL = 'http://api.weatherapi.com/v1/forecast.json'

@app.get("/weather/5days")
def get_weather_forecast(city: str):
    # Envoyer une requête à WeatherAPI
    response = requests.get(BASE_URL, params={
        'key': API_KEY,
        'q': city,
        'days': 5,         
        'aqi': 'no',       
        'alerts': 'no'     
    })


    #  Analyser les données JSON    
    weather_data = response.json()

    # Extraire les données des prévisions météorologiques pour les 5 prochains jours
    forecasts = []
    for day in weather_data['forecast']['forecastday']:
        forecasts.append({
            'date': day['date'],
            'max_temp': day['day']['maxtemp_c'],
            'min_temp': day['day']['mintemp_c'],
            'condition': day['day']['condition']['text']
        })

    # Retourner les données structurées
    return {
        'city': weather_data['location']['name'],
        'region': weather_data['location']['region'],
        'country': weather_data['location']['country'],
        'forecasts': forecasts
    }



# Connecter le fichier HTML au serveur
@app.get("/home", response_class=HTMLResponse)
def render_consumption_page(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/consumption", response_class=HTMLResponse)
def render_consumption_page(request: Request):
    return templates.TemplateResponse("consumption.html", {"request": request})

@app.get("/sensors_status", response_class=HTMLResponse)
def render_consumption_page(request: Request):
    return templates.TemplateResponse("sensors_status.html", {"request": request})

@app.get("/savings", response_class=HTMLResponse)
def render_consumption_page(request: Request):
    return templates.TemplateResponse("savings.html", {"request": request})

@app.get("/configuration", response_class=HTMLResponse)
def render_consumption_page(request: Request):
    return templates.TemplateResponse("configuration.html", {"request": request})

@app.get("/insert", response_class=HTMLResponse)
def render_consumption_page(request: Request):
    return templates.TemplateResponse("insert.html", {"request": request})

@app.get("/temperature", response_class=HTMLResponse)
def render_consumption_page(request: Request):
    return templates.TemplateResponse("temperature.html", {"request": request})

@app.get("/weather", response_class=HTMLResponse)
def render_weather_page(request: Request):
    return templates.TemplateResponse("weather.html", {"request": request})





import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)