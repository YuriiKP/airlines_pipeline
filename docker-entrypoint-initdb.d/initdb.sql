DROP DATABASE IF EXISTS airlines_db;

CREATE DATABASE IF NOT EXISTS airlines_db;

CREATE OR REPLACE TABLE airlines_db.flights
(
    flight_id UInt64,
    aircraft_id FixedString(8),
    departure_airport FixedString(3),
    arrival_airport FixedString(3),
    scheduled_departure DateTime(),
    actual_departure DateTime(),
    scheduled_arrival DateTime(),
    actual_arrival DateTime()
)
ENGINE = MergeTree
ORDER BY flight_id;


CREATE OR REPLACE TABLE airlines_db.telemetry
(
    flight_id UInt64,
    timestamp DateTime(),
    altitude UInt16,
    speed UInt16,
)
ENGINE = MergeTree
ORDER BY flight_id;



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


-- INSERT INTO airlines_db.test (id) VALUES (1);