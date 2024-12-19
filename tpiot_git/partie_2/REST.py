from pydantic import BaseModel
import sqlite3
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

import requests

app = FastAPI()

# Classe pour représenter une facture
class Facture(BaseModel):
    logement_id: int
    fac_type: str
    fac_date: str  # Format de la date 'YYYY-MM-DD'
    montant: int
    valeur_consommee: str

# Classe pour représenter une mesure
class Mesure(BaseModel):
    valeur: str
    ca_id: int

# Fonction pour se connecter à la base de données
def get_db_connection():
    conn = sqlite3.connect('logement.db')
    conn.row_factory = sqlite3.Row
    return conn

# Récupérer toutes les données de la table logement
@app.get("/logement/")
def check_logement():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM logement")
    logement = c.fetchall()
    conn.close()
    
    # Convertir les résultats en une liste de dictionnaires
    res = [dict(row) for row in logement]
    return {"message": res}

# Ajouter une nouvelle facture dans la table facture
@app.post("/factures/")
def create_facture(facture: Facture):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO facture (logement_id, fac_type, fac_date, montant, valeur_consommee) VALUES (?, ?, ?, ?, ?)",
        (facture.logement_id, facture.fac_type, facture.fac_date, facture.montant, facture.valeur_consommee)
    )
    conn.commit()
    conn.close()
    return {"message": "Facture ajoutée avec succès"}

# Ajouter une nouvelle mesure dans la table mesure
@app.post("/mesures/")
def create_mesure(mesure: Mesure):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO mesure (valeur, ca_id) VALUES (?, ?)",
        (mesure.valeur, mesure.ca_id)
    )
    conn.commit()
    conn.close()
    return {"message": "Mesure ajoutée avec succès"}





# Générer un graphique à partir des données de la table facture
@app.get("/factures/chart", response_class=HTMLResponse)
def get_factures_chart():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT fac_type, montant FROM facture")
    factures = c.fetchall()
    conn.close()

    # Convertir les résultats en liste de tuples
    data = [(row['fac_type'], row['montant']) for row in factures]

    # Générer le contenu HTML avec Google Charts
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>chart</title>
        <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
        <script type="text/javascript">
            google.charts.load('current', {{'packages':['corechart']}});
            google.charts.setOnLoadCallback(drawChart);

            function drawChart() {{
                var data = google.visualization.arrayToDataTable([
                    ['type', 'montant'],
                    {','.join([f"['{type}', {montant}]" for type, montant in data])}
                ]);

                var options = {{
                    title: 'porpotion'
                }};

                var chart = new google.visualization.PieChart(document.getElementById('piechart'));
                chart.draw(data, options);
            }}
        </script>
    </head>
    <body>
        <h1>chart</h1>
        <div id="piechart" style="width: 900px; height: 500px;"></div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)







# Configurer l'API WeatherAPI
API_KEY = '15fd613ef60f4c1fbfe101051241511'
BASE_URL = 'http://api.weatherapi.com/v1/forecast.json'

# Récupérer les prévisions météo pour 5 jours
@app.get("/weather/5days")
def get_weather_forecast(city: str):
    # Envoyer une requête à WeatherAPI
    response = requests.get(BASE_URL, params={
        'key': API_KEY,
        'q': city,
        'days': 5,         # Prévisions pour 5 jours
        'aqi': 'no',       # Pas de données sur la qualité de l'air
        'alerts': 'no'     # Pas d'alertes météo
    })

    # Analyser les données JSON
    weather_data = response.json()

    # Extraire les prévisions pour les 5 jours
    forecasts = []
    for day in weather_data['forecast']['forecastday']:
        forecasts.append({
            'date': day['date'],
            'max_temp': day['day']['maxtemp_c'],
            'min_temp': day['day']['mintemp_c'],
            'condition': day['day']['condition']['text']
        })

    # Retourner les données organisées
    return {
        'city': weather_data['location']['name'],
        'region': weather_data['location']['region'],
        'country': weather_data['location']['country'],
        'forecasts': forecasts
    }

# Lancer le serveur FastAPI
import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)
