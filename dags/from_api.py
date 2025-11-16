import random
import json
import time
import logging

import pendulum
import clickhouse_connect
import duckdb
import pandas as pd

from airflow.sdk import dag, task
from airflow.exceptions import AirflowException
from airflow.models import Variable

from extensions.generate_data import get_flights_from_api, get_telemetry_from_api



ACCESS_KEY = Variable.get('ACCESS_KEY')
SECRET_KEY = Variable.get('SECRET_KEY')

args = {
    'owner': 'yurii',
    'start_date': pendulum.now(),
    'schedule': "@daily",
    'catchup': True,
    'retries': 3, 
    'retry_delay': pendulum.duration(hours=1) 
}


@dag(
    dag_id='from_api_to_csv',
    tags=["example"],
    default_args=args,
)
def from_api():
    '''

    '''

    @task()
    def flights_from_api_to_s3(**context):
        '''
        Получаем данные о полетах за один день из имитации api и добавляем метку времени загрузки
        и сохраняем в s3.

        Обрабатывает ошибки сети и повторяет запрос до 3 раз

        Идемпотентность в данном случае можно реализовать в clickhouse создав таблицу ReplacingMergeTree
        и удалять дубли по flight_id, если только он уникальный. Или комбинации order by flight_id, load_timestamp.
        '''
        retry = 3
        retry_delay = 5
        json_data = None
        
        for i in range(retry):
            try: 
                json_data = get_flights_from_api(**context)
                break
            except AirflowException:
                if i + 1 < retry:
                    logging.info(f'Ошибка сети, ожидание {retry_delay} секунд перед повтором') 
                    time.sleep(retry_delay)

        if json_data is None: 
            raise AirflowException('Не удалось получить данные из API после всех попыток')

        # Загружаем данные в пандас и добавляем метку времени
        df = pd.DataFrame(json.loads(json_data))
        df['load_timestamp'] = pd.to_datetime(pendulum.now().isoformat(sep=' ', timespec='minutes'))

        # Сохраняем данные о полетах в s3
        start_date = context['data_interval_start'].format('YYYY-MM-DD')
        path = f's3://prod/flights/{start_date}/{start_date}_flights.csv'

        con = duckdb.connect()
        con.register('flights_data', df)
        con.sql(
            f'''
            SET TIMEZONE = "UTC";
            INSTALL httpfs;
            LOAD httpfs;
            SET s3_url_style = "path";
            SET s3_endpoint = "minio:9000";
            SET s3_access_key_id = "{ACCESS_KEY}";
            SET s3_secret_access_key = "{SECRET_KEY}";
            SET s3_use_ssl = FALSE;

            COPY (
                SELECT *
                FROM flights_data
            ) TO "{path}"
            '''
        )
        logging.info(f"Данные перелетов загружены в {path}")

        return path
      

    @task()
    def load_flights_to_ch(path, **context):
        '''
        Забираем данные в csv из s3 и загружаем их в clickhouse.

        '''
        
        main_table = 'flights'     
        
        # Загружаем csv из s3 
        con = duckdb.connect()
        df = con.execute(
            f'''
            SET TIMEZONE = "UTC";
            INSTALL httpfs;
            LOAD httpfs;
            SET s3_url_style = "path";
            SET s3_endpoint = "minio:9000";
            SET s3_access_key_id = "{ACCESS_KEY}";
            SET s3_secret_access_key = "{SECRET_KEY}";
            SET s3_use_ssl = FALSE;

            SELECT * FROM read_csv_auto('{path}')
            '''
        ).fetch_df()


        # Загружаем данные в clickchouse
        client = clickhouse_connect.get_client(
            host='ch_server',
            port=8123,
            username='click',
            password='click',
            database='airlines_db'
        )

        client.insert_df(main_table, df)
        logging.info(f"Данные загружены в таблицу {main_table}")
        
        # # Чтобы реализовать идемпотентную загрузку создадим временую таблицу 
        # # потом после вставки заменим партицию в основной таблице за день загрузки (партиционирование у нас настроено по дням)
        # client.command(f"DROP TABLE IF EXISTS {staging_table}")
        # client.command(f"CREATE TABLE {staging_table} LIKE {main_table}")
        
        # client.insert_df(staging_table, df)
        # logging.info(f"Данные ({len(df)} строк) загружены во временную таблицу {staging_table}")
        
        # client.command(
        #     f"ALTER TABLE {main_table} REPLACE PARTITION '{{ ds }}' FROM {staging_table}"
        # )
        # logging.info(f"Партиция '{{ ds }}' в {main_table} заменена.")



    @task()
    def telemetry_from_api_to_s3(**context):
        '''
        Получаем данные о телеметрии из имитации api и сохраняем их в формате csv в s3

        Обрабатывает ошибки сети и повторяет запрос до 3 раз
        '''

        retry = 3
        retry_delay = 5
        json_data = None
        
        for i in range(retry):
            try: 
                json_data = get_telemetry_from_api(**context)
                break
            except AirflowException:
                if i + 1 < retry:
                    logging.info(f'Ошибка сети, ожидание {retry_delay} секунд перед повтором') 
                    time.sleep(retry_delay)

        if json_data is None: 
            raise AirflowException('Не удалось получить данные телеметрии из API после всех попыток')

        # Загружаем данные в пандас и добавляем метку времени
        df = pd.DataFrame(json.loads(json_data))
        # df['load_timestamp'] = pd.to_datetime(pendulum.now().isoformat(sep=' ', timespec='minutes'))

        # Сохраняем данные о полетах в s3
        start_date = context['data_interval_start'].format('YYYY-MM-DD')
        path = f's3://prod/telemetry/{start_date}/{start_date}_telemetry.csv'

        con = duckdb.connect()
        con.register('flights_data', df)
        con.sql(
            f'''
            SET TIMEZONE = "UTC";
            INSTALL httpfs;
            LOAD httpfs;
            SET s3_url_style = "path";
            SET s3_endpoint = "minio:9000";
            SET s3_access_key_id = "{ACCESS_KEY}";
            SET s3_secret_access_key = "{SECRET_KEY}";
            SET s3_use_ssl = FALSE;

            COPY (
                SELECT *
                FROM flights_data
            ) TO "{path}"
            '''
        )
        logging.info(f"Данные телеметрии загружены в {path}")

        return path

    @task()
    def load_telemetry_to_ch(path, **context):
        '''
        Загрузки телеметрии в clickhouse.

        - Чтение csv-файла из S3.
        - Загрузка данных во временную таблицу clickhouse.
        - Перезапись соответствующей партиции основной таблицы (идемпотентная загрузка).
        '''

        main_table = 'telemetry'
        staging_table = 'tmp_telemetry'
        start_date = context['data_interval_start'].format('YYYYMMDD')
        
        # Загружаем csv из s3 
        con = duckdb.connect()
        df = con.execute(
            f'''
            SET TIMEZONE = "UTC";
            INSTALL httpfs;
            LOAD httpfs;
            SET s3_url_style = "path";
            SET s3_endpoint = "minio:9000";
            SET s3_access_key_id = "{ACCESS_KEY}";
            SET s3_secret_access_key = "{SECRET_KEY}";
            SET s3_use_ssl = FALSE;

            SELECT * FROM read_csv_auto('{path}')
            '''
        ).fetch_df()

        # Загружаем данные в clickchouse
        client = clickhouse_connect.get_client(
            host='ch_server',
            port=8123,
            username='click',
            password='click',
            database='airlines_db'
        )

        # Чтобы реализовать идемпотентную загрузку создадим временую таблицу 
        # потом после вставки заменим партицию в основной таблице за день загрузки (партиционирование у нас настроено по дням)
        client.command(f"DROP TABLE IF EXISTS {staging_table}")
        client.command(f"CREATE TABLE {staging_table} AS {main_table}")
        
        client.insert_df(staging_table, df)
        logging.info(f"Данные ({len(df)} строк) загружены во временную таблицу {staging_table}")
        
        client.command(
            f"ALTER TABLE {main_table} REPLACE PARTITION '{start_date}' FROM {staging_table}"
        )
        logging.info(f"Партиция '{start_date}' в {main_table} заменена.")

    
    
    flights_path = flights_from_api_to_s3()
    load_flights_to_ch(flights_path)
    telemetry_path = telemetry_from_api_to_s3()
    load_telemetry_to_ch(telemetry_path)


from_api()