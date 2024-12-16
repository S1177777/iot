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
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/api/consumption")
def get_consumption_data():
    conn = get_db_connection()
    c = conn.cursor()

    # 获取每个房间的最新测量值
    c.execute('''
        SELECT 
            p.piece_nom,
            MAX(CASE WHEN t.nom_type = 'temperature' THEN m.valeur ELSE NULL END) AS latest_temperature,
            MAX(CASE WHEN t.nom_type = 'humidity' THEN m.valeur ELSE NULL END) AS latest_humidity,
            MAX(CASE WHEN t.nom_type = 'electric' THEN m.valeur ELSE NULL END) AS latest_electric,
            MAX(CASE WHEN t.nom_type = 'AQI' THEN m.valeur ELSE NULL END) AS latest_AQI
        FROM 
            piece p
        JOIN 
            capteuractionneur c ON p.piece_id = c.piece_id
        JOIN 
            type t ON c.type_id = t.type_id
        LEFT JOIN 
            mesure m ON c.ca_id = m.ca_id
        WHERE 
            m.dateinsert = (
                SELECT MAX(m2.dateinsert)
                FROM mesure m2
                WHERE m2.ca_id = c.ca_id
            )
        GROUP BY 
            p.piece_nom;
    ''')
    room_data = c.fetchall()

    # 获取最新总电量消耗
    c.execute('''
        SELECT 
            SUM(CAST(m.valeur AS FLOAT)) AS total_electric
        FROM 
            capteuractionneur c
        JOIN 
            type t ON c.type_id = t.type_id
        LEFT JOIN 
            mesure m ON c.ca_id = m.ca_id
        WHERE 
            t.nom_type = 'electric' AND
            m.dateinsert = (
                SELECT MAX(m2.dateinsert)
                FROM mesure m2
                WHERE m2.ca_id = c.ca_id
            );
    ''')
    total_electric = c.fetchone()["total_electric"]

    conn.close()

    # 返回 JSON 数据
    return JSONResponse(content={
        "room_data": [dict(row) for row in room_data],
        "total_electric": total_electric
    })






@app.get("/api/sensors_status")
def get_sensors_status():
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # 执行查询获取传感器状态信息
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

        # 转换查询结果为 JSON 格式
        return {"sensors": [dict(row) for row in sensors_data]}

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/api/savings")
def get_savings_data():
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # 查询总用电量
        c.execute('''
            SELECT 
                SUM(CAST(m.valeur AS FLOAT)) AS total_electric
            FROM 
                mesure m
            JOIN 
                capteuractionneur c ON m.ca_id = c.ca_id
            JOIN 
                type t ON c.type_id = t.type_id
            WHERE 
                t.nom_type = 'electric';
        ''')
        total_electric = c.fetchone()["total_electric"] or 0

        # 查询账单金额
        c.execute('''
            SELECT 
                fac_date, montant
            FROM 
                facture
            WHERE 
                fac_type = 'electricité'
            ORDER BY 
                fac_date;
        ''')
        bills_data = c.fetchall()

        conn.close()

        # 返回 JSON 数据
        return {
            "total_electric": total_electric,
            "bills": [dict(row) for row in bills_data]
        }

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)




#编写一个 API 路由，返回所有传感器及其当前的 is_visible 状态
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

#创建一个 API 路由，用于更新指定传感器的 is_visible 状态
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


#创建一个 API 路由 /api/sensors/types，返回所有传感器的 ca_id 和对应的类型 type_id
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



#创建一个 API 路由 /api/sensors/insert_measure，用于将用户输入的值插入到 mesure 表中
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


# 配置你的 API 密钥和基础 URL（使用 WeatherAPI）
API_KEY = '15fd613ef60f4c1fbfe101051241511'
BASE_URL = 'http://api.weatherapi.com/v1/forecast.json'

@app.get("/weather/5days")
def get_weather_forecast(city: str):
    # 发送请求到 WeatherAPI
    response = requests.get(BASE_URL, params={
        'key': API_KEY,
        'q': city,
        'days': 5,         # 获取未来 5 天的天气预报
        'aqi': 'no',       # 不需要空气质量数据
        'alerts': 'no'     # 不需要天气警报数据
    })


    # 解析 JSON 数据
    weather_data = response.json()

    # 提取未来 5 天的天气预报数据
    forecasts = []
    for day in weather_data['forecast']['forecastday']:
        forecasts.append({
            'date': day['date'],
            'max_temp': day['day']['maxtemp_c'],
            'min_temp': day['day']['mintemp_c'],
            'condition': day['day']['condition']['text']
        })

    # 返回整理后的数据
    return {
        'city': weather_data['location']['name'],
        'region': weather_data['location']['region'],
        'country': weather_data['location']['country'],
        'forecasts': forecasts
    }




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




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)