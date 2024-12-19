--delete all tables Question 2
DROP TABLE IF EXISTS logement;
DROP TABLE IF EXISTS piece;
DROP TABLE IF EXISTS capteuractionneur;
DROP TABLE IF EXISTS type;
DROP TABLE IF EXISTS mesure;
DROP TABLE IF EXISTS facture;


--Question 3
CREATE TABLE logement (
    logement_id INTEGER PRIMARY KEY AUTOINCREMENT,
    adresse VARCHAR(255) NOT NULL,
    numtele INTEGER NOT NULL,
    IP VARCHAR(255) NOT NULL,
    dateinsert TIMESTAMP DEFAULT CURRENT_TIMESTAMP     
);


CREATE TABLE piece (
    piece_id INTEGER PRIMARY KEY AUTOINCREMENT,
    piece_nom VARCHAR(100) NOT NULL,
    logement_id INTEGER,
    coord_x INTEGER NOT NULL,
    coord_y INTEGER NOT NULL,
    coord_z INTEGER NOT NULL,
    FOREIGN KEY (logement_id) REFERENCES logement(logement_id)    
);

CREATE TABLE capteuractionneur (
    ca_id INTEGER PRIMARY KEY AUTOINCREMENT,
    reference_commmerciale TEXT NOT NULL,
    piece_id INTEGER,
    type_id INTEGER,
    ca_type VARCHAR(100),
    port_communication VARCHAR(100) NOT NULL,
    dateinsert TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (piece_id) REFERENCES piece(piece_id),
    FOREIGN KEY (type_id) REFERENCES type(type_id)    
);

ALTER TABLE capteuractionneur ADD COLUMN is_visible BOOLEAN DEFAULT 1;--html


CREATE TABLE mesure (
    mes_id INTEGER PRIMARY KEY AUTOINCREMENT,
    valeur TEXT NOT NULL,
    ca_id INTEGER,
    dateinsert TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ca_id) REFERENCES capteuractionneur(ca_id)      
);

CREATE TABLE type (
    type_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom_type VARCHAR(100) NOT NULL,
    unite_mes VARCHAR(100) NOT NULL,
    plage_precision VARCHAR(100),
    information VARCHAR(100)  
);

CREATE TABLE facture (
    fac_id INTEGER PRIMARY KEY AUTOINCREMENT,
    logement_id INTEGER,
    fac_type VARCHAR(100) NOT NULL,
    fac_date INTEGER NOT NULL,
    montant INTEGER NOT NULL,
    valeur_consommee VARCHAR(100) NOT NULL,
    FOREIGN KEY (logement_id) REFERENCES logement(logement_id)    
);


--pour DHT11
CREATE TABLE temperature_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    temperature FLOAT NOT NULL,
    humidity FLOAT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);


--Question 4
--1 logement avec 4 pieces
INSERT INTO logement (adresse, numtele, IP)
VALUES ('France', '0745673546', '172.20.10.3');

INSERT INTO piece (logement_id, piece_nom, coord_x, coord_y, coord_z)
VALUES 
(1, '201', 1, 1, 1),
(1, '202', 2, 2, 2),
(1, '203', 3, 3, 3),
(1, '204', 4, 4, 4);


--Question 5
--créer au moins 4 types de capteurs/actionneurs
INSERT INTO type (nom_type, unite_mes, plage_precision, information)
VALUES 
('temperature', '°C', '0.1', 'none'),
('humidite', '%', '0.1', 'none'),
('electric', 'kWh', '0.1', 'none'),
('AQI', 'none', '0.1', 'none');



--Question 6
INSERT INTO capteuractionneur (reference_commmerciale, piece_id, type_id, ca_type, port_communication)
SELECT 'DHT11', 1, 1, t.nom_type, '1111'
FROM type t
WHERE t.type_id = 1
UNION ALL
SELECT 'elecmesure', 2, 3, t.nom_type, '2222'
FROM type t
WHERE t.type_id = 3;



--Question 7
INSERT INTO mesure (valeur, ca_id)
SELECT '25.5°C', ca.ca_id
FROM capteuractionneur ca
WHERE ca.ca_id = 1;

INSERT INTO mesure (valeur, ca_id)
SELECT '26.0°C', ca.ca_id
FROM capteuractionneur ca
WHERE ca.ca_id = 1;

INSERT INTO mesure (valeur, ca_id)
SELECT '150kWh', ca.ca_id
FROM capteuractionneur ca
WHERE ca.ca_id = 2;

INSERT INTO mesure (valeur, ca_id)
SELECT '155kWh', ca.ca_id
FROM capteuractionneur ca
WHERE ca.ca_id = 2;


--Question 8
INSERT INTO facture (logement_id, fac_type, fac_date, montant, valeur_consommee) 
VALUES 
(1, 'electricité', '2024-01-01', 120, '100 kWh'),
(1, 'electricité', '2024-02-01', 130, '110 kWh'),
(1, 'electricité', '2024-01-15', 150, '125 kWh'),
(1, 'electricité', '2024-02-15', 145, '120 kWh');


