-- Create a user and grant privileges
CREATE USER 'auth_user'@'localhost' IDENTIFIED BY 'auth123';

-- Create a database named 'auth'
CREATE DATABASE auth;

-- Grant all privileges on the 'auth' database to 'auth_user'
GRANT ALL PRIVILEGES ON auth.* TO 'auth_user'@'localhost';

-- Switch to the 'auth' database
USE auth;

-- Create a 'user' table
CREATE TABLE user (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

-- Insert a user into the 'user' table
INSERT INTO user (email, password) VALUES ('jcolamaio@mail.com', 'admin123');
