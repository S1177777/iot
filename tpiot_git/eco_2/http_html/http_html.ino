#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <DHT.h>

// Configuration du WiFi
const char* ssid = "test1"; // Nom du réseau WiFi
const char* password = "rylszzzz"; // Mot de passe WiFi

// URL du serveur Node-RED
String serverUrl = "http://172.20.10.3:8000/api/sensors/temperature"; 

// Configuration du capteur DHT11
#define DHTPIN 13  // Broche connectée au DHT11
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE); // Initialisation du capteur DHT11

// Création de l'objet WiFiClient
WiFiClient wifiClient;

void setup() {
  Serial.begin(115200);
  
  // Connexion au WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print("Statut : ");
    Serial.println(WiFi.status());  // Afficher le statut WiFi
  }

  Serial.println("Connexion réussie");
  Serial.println(WiFi.localIP()); // Adresse IP locale

  // Initialisation du capteur DHT
  dht.begin();
}

void loop() {
  // Lecture des données de température et d'humidité
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  // Vérification de la lecture
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("Erreur de lecture des données.");
    return;
  }

  // Affichage des données
  Serial.println("Température : " + String(temperature) + "°C");
  Serial.println("Humidité : " + String(humidity) + "%");

  // Création d'un client HTTP
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    // Initialisation de la connexion HTTP avec l'URL
    http.begin(wifiClient, serverUrl);
    http.addHeader("Content-Type", "application/json"); // Définir le type de contenu JSON

    // Préparation des données JSON
    String jsonData = "{\"temperature\": " + String(temperature) + ", \"humidity\": " + String(humidity) + "}";

    // Envoi de la requête POST
    int httpResponseCode = http.POST(jsonData);

    // Vérification et affichage de la réponse HTTP
    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("Réponse HTTP : " + response);
    } else {
      Serial.print("Échec du POST, code d'erreur : ");
      Serial.println(httpResponseCode);  // Afficher le code d'erreur HTTP
    }

    // Fin de la requête HTTP
    http.end();
  }

  // Envoi des données toutes les 10 secondes
  delay(10000);
}
