import random
import json
import time
import logging

import pendulum
from faker import Faker
import pandas as pd



FLIGHTS = ['SU1234', 'SU5678', 'SU5742', 'SU1029']
AIRCRAFTS = ['A320-001', 'A321-002', 'B737-003', 'A324-005']
AIRPORTS = ['SVO', 'LED', 'VKO', 'DME', 'AER', 'OVB']



class SimulatedNetworkError(Exception):
    """Исключение для имитации сбоя сети."""
    pass


def get_flights_from_api(n:int = 100):
    '''
    Метод генерирует ответ из внешнего API со списом всех рейсов за один день

    Логики полета борта "туда обратно" нет. здесь может быть вариант, когда
    один и тотже самолет находится в воздухе. Но исходя из условия задачи это не столь важно.
    '''
    
    faker = Faker()

    flights = []
    for _ in range(n):        
        flight_id = random.choice(FLIGHTS)
        aircraft_id = random.choice(AIRCRAFTS)
        port1, port2 = random.sample(AIRPORTS, 2)

        flight_duration = pendulum.duration(minutes=random.randint(60, 180))

        scheduled_departure = faker.date_time_between('-1day', pendulum.now())
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


def api_data_to_csv():
    '''
    Сохраняет данные в формате в csv полученные из имитации api в дирректорию './data/*.csv', за определенные день
    '''
    retry = 3
    retry_delay = 5
    json_data = None
    
    for i in range(retry):
        try: 
            json_data = get_flights_from_api()
            break
        except SimulatedNetworkError:
            if i + 1 < retry:
                logging.info(f'Ошибка сети, ожидание {retry_delay} секунд перед повтором') 
                time.sleep(retry_delay)

    if json_data is None: 
        logging.warning('Не удалось получить данные из API после всех попыток')
        return

    df = pd.DataFrame(json.loads(json_data))

    df['load_timestamp'] = pendulum.now().isoformat(sep=' ', timespec='minutes')
    path = f'./data/flights_from_api_{pendulum.now().date()}.csv'
    df.to_csv(path)
    logging.info(f'Данные сохранены по пути {path}')



if __name__ == "__main__":
    api_data_to_csv()