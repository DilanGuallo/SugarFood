-- Datos de prueba para Azca Project
-- Ejecutar después de crear las tablas con init_db.sql en MySQL
-- Las contraseñas están hasheadas con bcrypt (password original: 'password123')

-- Usuarios de prueba
INSERT INTO usuarios_azca (nombre_usuario, email, password, rol, telefono) VALUES
('La Taberna de Azca', 'taberna@azca.com', '$2b$12$qM8sXn8tWX4Rw6zU4q13a.qwhQFkGtQ6CVnSjHeicT2Otnq4knZMG', 'Bar', '+34 911 123 456'),
('El Rincón Castellano', 'rincon@azca.com', '$2b$12$qM8sXn8tWX4Rw6zU4q13a.qwhQFkGtQ6CVnSjHeicT2Otnq4knZMG', 'Bar', '+34 911 234 567'),
('Café del Prado', 'cafe@azca.com', '$2b$12$qM8sXn8tWX4Rw6zU4q13a.qwhQFkGtQ6CVnSjHeicT2Otnq4knZMG', 'Bar', '+34 911 345 678'),
('María González', 'maria@email.com', '$2b$12$qM8sXn8tWX4Rw6zU4q13a.qwhQFkGtQ6CVnSjHeicT2Otnq4knZMG', 'Cliente', '+34 600 123 456'),
('Carlos Rodríguez', 'carlos@email.com', '$2b$12$qM8sXn8tWX4Rw6zU4q13a.qwhQFkGtQ6CVnSjHeicT2Otnq4knZMG', 'Cliente', '+34 600 234 567'),
('Ana López', 'ana@email.com', '$2b$12$qM8sXn8tWX4Rw6zU4q13a.qwhQFkGtQ6CVnSjHeicT2Otnq4knZMG', 'Cliente', '+34 600 345 678');

-- Menús de prueba
INSERT INTO menus_azca (menu_del_dia, precio, platos, bar_rest, dia, fecha, telefono, aperitivo, usuario_id) VALUES
('Menú Ejecutivo', '14.50€', 'Platos tradicionales madrileños', 'La Taberna de Azca', 'Lunes', '2026-03-17', '+34 911 123 456', 'Pan con alioli', 1),
('Menú del Día', '12.90€', 'Cocina casera española', 'El Rincón Castellano', 'Martes', '2026-03-18', '+34 911 234 567', 'Aceitunas y pan', 2),
('Menú Vegetariano', '13.75€', 'Platos vegetarianos saludables', 'Café del Prado', 'Miércoles', '2026-03-19', '+34 911 345 678', 'Hummus con crudités', 3);

-- Primeros platos
INSERT INTO primeros_platos (menu_id, nombre) VALUES
(1, 'Salmorejo cordobés con crujiente de jamón'),
(1, 'Ensalada de queso de cabra y nueces'),
(1, 'Risotto de setas trufado'),
(2, 'Lentejas estofadas con chorizo'),
(2, 'Gazpacho manchego'),
(2, 'Crema de calabaza con virutas de jamón'),
(3, 'Quinoa con verduras asadas'),
(3, 'Tartar de tomate y aguacate'),
(3, 'Crema de verduras de temporada');

-- Segundos platos
INSERT INTO segundos_platos (menu_id, nombre) VALUES
(1, 'Entrecot a la parrilla con patatas'),
(1, 'Lomo de salmón al horno'),
(1, 'Secreto ibérico con pimientos'),
(2, 'Cochinillo asado'),
(2, 'Merluza a la romana'),
(2, 'Pollo al chilindrón'),
(3, 'Tofu salteado con verduras'),
(3, 'Falafel con tabbouleh'),
(3, 'Hamburguesa de lentejas');

-- Complementos
INSERT INTO complementos (menu_id, nombre) VALUES
(1, 'Pan de pueblo'),
(1, 'Bebida (agua, vino o refresco)'),
(1, 'Café'),
(2, 'Pan'),
(2, 'Bebida'),
(2, 'Postre de la casa'),
(3, 'Pan integral'),
(3, 'Zumo natural'),
(3, 'Infusión');

-- Postres
INSERT INTO postres (menu_id, nombre) VALUES
(1, 'Tarta de queso con frutos rojos'),
(1, 'Flan de huevo casero'),
(1, 'Fruta del tiempo'),
(2, 'Arroz con leche'),
(2, 'Natillas'),
(2, 'Yogur con miel'),
(3, 'Mousse de chocolate negro'),
(3, 'Compota de manzana'),
(3, 'Frutos secos y fruta');

-- Menús infantiles
INSERT INTO menus_infantiles (menu_id, nombre) VALUES
(1, 'Macarrones con queso'),
(1, 'Pollo con patatas fritas'),
(1, 'Helado de vainilla'),
(2, 'Spaghetti con tomate'),
(2, 'Pechuga de pollo empanada'),
(2, 'Galletas caseras'),
(3, 'Pasta integral con verduras'),
(3, 'Hamburguesa de verduras'),
(3, 'Yogur natural con frutas');

-- Verificar datos insertados
SELECT 'Usuarios:' as tabla, COUNT(*) as cantidad FROM usuarios_azca
UNION ALL
SELECT 'Menús:', COUNT(*) FROM menus_azca
UNION ALL
SELECT 'Primeros platos:', COUNT(*) FROM primeros_platos
UNION ALL
SELECT 'Segundos platos:', COUNT(*) FROM segundos_platos
UNION ALL
SELECT 'Complementos:', COUNT(*) FROM complementos
UNION ALL
SELECT 'Postres:', COUNT(*) FROM postres
UNION ALL
SELECT 'Menús infantiles:', COUNT(*) FROM menus_infantiles;