DROP DATABASE IF EXISTS airlines_db;

CREATE DATABASE IF NOT EXISTS airlines_db;

CREATE OR REPLACE TABLE airlines_db.flights
(
    flight_id FixedString(6),
    aircraft_id FixedString(8),
    departure_airport FixedString(3),
    arrival_airport FixedString(3),
    scheduled_departure DateTime(),
    actual_departure DateTime(),
    scheduled_arrival DateTime(),
    actual_arrival DateTime(),
    load_timestamp DateTime()
)
ENGINE = MergeTree
ORDER BY flight_id
PARTITION BY  toYYYYMM(load_timestamp);


-- Задание 1 
-- Чтобы убедиться в правильности данных в данном случае, можно было бы сократить 
-- выборку до нескольких рейсов и проверить правильность расчетов вручную.
-- Также проверить адекватность результата, например если средняя задержка слишком большая, или вообще нулевая.
CREATE VIEW airlines_db.v_flights AS
SELECT
    aircraft_id,
    avg(actual_departure - scheduled_departure) AS avg_departure_delay,
    avg(actual_arrival - scheduled_arrival) AS avg_arrival_delay,
    avg((actual_departure - scheduled_departure) > 900) * 100 AS delayed_over_15_min
FROM
    airlines_db.flights
WHERE
    actual_departure > 0 
    AND actual_arrival > 0
GROUP BY
    aircraft_id;


-- Задание 3
-- Выбрал старнартный движок из семейства MergeTree, думаю он подойдет.
-- Сортировка по двум полям (flight_id, aircraft_id) выбрана из предположения, что часто нужно будет фильтроваться по id полета и id судна.
-- Партиционирование выбрал по дням. Данных очень много, поэтому сделал выбор в сторону партиционирования по дням.
-- ttl по умолчанию удаляет строки, как альтернатива можно поменять сжатие и переместить данные вдругое место.
CREATE OR REPLACE TABLE airlines_db.telemetry
(
    aircraft_id FixedString(8),
    flight_id FixedString(6),
    timestamp DateTime(),
    parameter LowCardinality(String), 
    value Float32()
)
ENGINE = MergeTree 
ORDER BY (flight_id, aircraft_id) 
PARTITION BY  toYYYYMMDD(timestamp) 
TTL timestamp + INTERVAL 1 YEAR;



-- Задание 2 
CREATE VIEW airlines_db.v_telemetry AS
SELECT
    flight_id,
    MAX(
        CASE 
            WHEN parameter = 'altitude' THEN value 
            ELSE NULL 
        END
    ) AS max_altitude_m,
    AVG(
        CASE 
            WHEN parameter = 'speed' THEN value 
            ELSE NULL 
        END
    ) AS avg_speed_kmh,
    MIN(
        CASE 
            WHEN parameter = 'altitude' AND value > 1000 THEN timestamp 
            ELSE NULL 
        END
    ) AS first_1000m

FROM
    airlines_db.telemetry
GROUP BY
    flight_id;