-- Script SQL para inicializar la base de datos Azca Project
-- Ejecutar este script en MySQL para crear las tablas

-- Crear la base de datos (si no existe)
-- CREATE DATABASE IF NOT EXISTS azca_db;

-- Usar la base de datos
-- USE azca_db;

-- Tabla para usuarios (login)
CREATE TABLE IF NOT EXISTS usuarios_azca (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre_usuario VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    rol VARCHAR(50) CHECK (rol IN ('Bar', 'Cliente')) NOT NULL,
    telefono VARCHAR(20)
);

-- Tabla para menús extraídos por IA
CREATE TABLE IF NOT EXISTS menus_azca (
    id INT AUTO_INCREMENT PRIMARY KEY,
    menu_del_dia TEXT,
    precio TEXT,
    platos TEXT,
    bar_rest TEXT,
    dia TEXT,
    fecha DATE,
    telefono TEXT,
    aperitivo TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_id INT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios_azca(id) ON DELETE CASCADE
);

-- Tabla para primeros platos
CREATE TABLE IF NOT EXISTS primeros_platos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    menu_id INT,
    nombre TEXT NOT NULL,
    FOREIGN KEY (menu_id) REFERENCES menus_azca(id) ON DELETE CASCADE
);

-- Tabla para segundos platos
CREATE TABLE IF NOT EXISTS segundos_platos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    menu_id INT,
    nombre TEXT NOT NULL,
    FOREIGN KEY (menu_id) REFERENCES menus_azca(id) ON DELETE CASCADE
);

-- Tabla para complementos
CREATE TABLE IF NOT EXISTS complementos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    menu_id INT,
    nombre TEXT NOT NULL,
    FOREIGN KEY (menu_id) REFERENCES menus_azca(id) ON DELETE CASCADE
);

-- Tabla para postres
CREATE TABLE IF NOT EXISTS postres (
    id INT AUTO_INCREMENT PRIMARY KEY,
    menu_id INT,
    nombre TEXT NOT NULL,
    FOREIGN KEY (menu_id) REFERENCES menus_azca(id) ON DELETE CASCADE
);

-- Tabla para menús infantiles
CREATE TABLE IF NOT EXISTS menus_infantiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    menu_id INT,
    nombre TEXT NOT NULL,
    FOREIGN KEY (menu_id) REFERENCES menus_azca(id) ON DELETE CASCADE
);

-- Tabla para valoraciones y reseñas
CREATE TABLE IF NOT EXISTS valoraciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    menu_id INT NOT NULL,
    usuario_id INT NOT NULL,
    puntuacion INT CHECK (puntuacion BETWEEN 1 AND 5) NOT NULL,
    resena TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (menu_id) REFERENCES menus_azca(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios_azca(id) ON DELETE CASCADE,
    UNIQUE KEY unique_review (menu_id, usuario_id)
);

-- Índices para mejorar rendimiento
CREATE INDEX idx_usuarios_email ON usuarios_azca(email);
CREATE INDEX idx_usuarios_rol ON usuarios_azca(rol);
CREATE INDEX idx_menus_usuario ON menus_azca(usuario_id);
CREATE INDEX idx_menus_fecha ON menus_azca(fecha_creacion);
CREATE INDEX idx_primeros_menu ON primeros_platos(menu_id);
CREATE INDEX idx_segundos_menu ON segundos_platos(menu_id);
CREATE INDEX idx_complementos_menu ON complementos(menu_id);
CREATE INDEX idx_postres_menu ON postres(menu_id);
CREATE INDEX idx_infantiles_menu ON menus_infantiles(menu_id);