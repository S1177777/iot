import sqlite3, random
from datetime import datetime, timedelta

# ouverture/initialisation de la base de donnee
conn = sqlite3.connect('logement.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()



# Génération et insertion de plusieurs mesures dans la base de données
def ajouter_mesures(c, nombre_mesures=10):
    c.execute("SELECT ca_id FROM capteuractionneur")
    capteur_ids = [row['ca_id'] for row in c.fetchall()]

    for _ in range(nombre_mesures):
        ca_id = random.choice(capteur_ids)
        valeur = f"{random.uniform(20.0, 100.0):.2f} {random.choice(['°C', 'kWh', '%'])}"
        c.execute(
            "INSERT INTO mesure (valeur, ca_id, dateinsert) VALUES (?, ?, ?)",
            (valeur, ca_id, date_insertion)
        )

# Génération et insertion de plusieurs factures dans la base de données
def ajouter_factures(c, nombre_factures=5):
    c.execute("SELECT logement_id FROM logement")
    logement_ids = [row['logement_id'] for row in c.fetchall()]

    for _ in range(nombre_factures):
        logement_id = random.choice(logement_ids)
        fac_type = random.choice(['Electricité', 'Eau', 'Gaz'])
        fac_date = datetime.now().strftime('%Y-%m-%d')  # Date actuelle
        montant = random.randint(50, 500)  # Montant aléatoire entre 50 et 500
        valeur_consommee = f"{random.uniform(100.0, 1000.0):.2f} kWh"  # Valeur consommée aléatoire
        c.execute(
            "INSERT INTO facture (logement_id, fac_type, fac_date, montant, valeur_consommee) VALUES (?, ?, ?, ?, ?)",
            (logement_id, fac_type, fac_date, montant, valeur_consommee)
        )

# Appels des fonctions pour ajouter les mesures et factures
ajouter_mesures(c, nombre_mesures=10)  # Ajoute 10 mesures
ajouter_factures(c, nombre_factures=10)  # Ajoute 10 factures

# fermeture
conn.commit()
conn.close()

