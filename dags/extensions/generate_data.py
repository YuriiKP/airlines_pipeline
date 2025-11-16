import random
import json

import pendulum

from faker import Faker



FLIGHTS = ['SU1234', 'SU5678', 'SU5742', 'SU1029']
AIRCRAFTS = ['A320-001', 'A321-002', 'B737-003', 'A324-005']
AIRPORTS = ['SVO', 'LED', 'VKO', 'DME', 'AER', 'OVB']


def get_flights_from_api(n:int = 100, **context):
    '''
    Метод генерирует ответ из внешнего API со списом всех рейсов за один день

    Логики полета борта "туда обратно" нет. здесь может быть вариант, когда
    один и тотже самолет находится в воздухе. Но исходя из условия задачи это не столь важно.
    '''
    
    start_date = context['data_interval_start']
    print(f'Время запуска {start_date}')
    
    faker = Faker()

    flights = []
    for _ in range(n):        
        flight_id = random.choice(FLIGHTS)
        aircraft_id = random.choice(AIRCRAFTS)
        port1, port2 = random.sample(AIRPORTS, 2)

        flight_duration = pendulum.duration(minutes=random.randint(60, 180))

        scheduled_departure = faker.date_time_between(start_date - pendulum.duration(days=1), start_date)
        actual_departure = scheduled_departure + pendulum.duration(minutes=random.randint(-20, 20))

        scheduled_arrival = scheduled_departure + flight_duration
        actual_arrival = actual_departure + flight_duration

        
        dict_flight = {
            'flight_id': flight_id,
            'aircraft_id': aircraft_id,
            'departure_airport': port1,
            'arrival_airport': port2,
            'scheduled_departure': scheduled_departure.isoformat(sep=' ', timespec='minutes'),
            'actual_departure': actual_departure.isoformat(sep=' ', timespec='minutes'),
            'scheduled_arrival': scheduled_arrival.isoformat(sep=' ', timespec='minutes'),
            'actual_arrival': actual_arrival.isoformat(sep=' ', timespec='minutes'),
        }

        flights.append(dict_flight)

    return json.dumps(flights)


def get_telemetry_from_api(n:int = 10000, **context):
    '''
    Метод генерирует ответ из внешнего API с телеметрией самолетов
    
    Генерирует телеметрические данные от датчиков самолетов в формате JSON
    '''
    
    start_date = context['data_interval_start']
    print(f'Время запуска {start_date}')
    
    faker = Faker()
    
    # Параметры телеметрии
    TELEMETRY_PARAMETERS = {
        'engine_temperature': (200.0, 450.0),  
        'altitude': (0.0, 12000.0),  
        'speed': (0.0, 900.0),
    }
    
    telemetry_records = []
    
    for _ in range(n):
        flight_id = random.choice(FLIGHTS)
        aircraft_id = random.choice(AIRCRAFTS)
        parameter = random.choice(list(TELEMETRY_PARAMETERS.keys()))
        min_val, max_val = TELEMETRY_PARAMETERS[parameter]
        value = round(random.uniform(min_val, max_val), 2)
        
        timestamp = faker.date_time_between(start_date - pendulum.duration(days=1), start_date)
        
        telemetry_record = {
            'aircraft_id': aircraft_id,
            'flight_id': flight_id,
            'timestamp': timestamp.isoformat(sep=' ', timespec='seconds'),
            'parameter': parameter,
            'value': value
        }
        
        telemetry_records.append(telemetry_record)
    
    return json.dumps(telemetry_records)
