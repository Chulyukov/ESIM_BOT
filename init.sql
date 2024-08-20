CREATE DATABASE IF NOT EXISTS esim_db;

USE esim_db;

CREATE TABLE IF NOT EXISTS bnesim_products (
    product_id VARCHAR(255) PRIMARY KEY,
    country VARCHAR(255),
    volume INT,
    price VARCHAR(255),
    percentage_of_profit VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS users (
    chat_id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(255),
    activation_datetime DATETIME,
    cli VARCHAR(255),
    data JSON,
    top_up_data JSON,
    top_up_flag TINYINT(1) DEFAULT 0
);