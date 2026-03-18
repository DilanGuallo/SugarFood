# Servicio para MySQL
import mysql.connector
from mysql.connector import cursor
import json
import bcrypt
from ..models.schemas import UsuarioCreate, MenuAzca

def hash_password(password: str) -> str:
    """Hashea una contraseña usando bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verifica una contraseña contra su hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def get_db_connection():
    # Leer configuración desde el archivo JSON
    with open('../config/connections.json', 'r') as f:
        config = json.load(f)

    db_config = config['database']

    # Conexión a MySQL
    conn = mysql.connector.connect(
        host=db_config['host'],
        port=db_config.get('port', 3306),
        database=db_config['database'],
        user=db_config['user'],
        password=db_config['password']
    )
    return conn

def create_usuario(usuario: UsuarioCreate) -> int:
    conn = get_db_connection()
    with conn.cursor() as cursor:
        # Hashear la contraseña
        hashed_password = hash_password(usuario.password)
        cursor.execute("""
            INSERT INTO usuarios_azca (nombre_usuario, email, password, rol, telefono)
            VALUES (%s, %s, %s, %s, %s)
        """, (usuario.nombre_usuario, usuario.email, hashed_password, usuario.rol, usuario.telefono))
        user_id = cursor.lastrowid
        conn.commit()
    conn.close()
    return user_id

def get_usuario_by_email(email: str):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM usuarios_azca WHERE email = %s", (email,))
        result = cursor.fetchone()
        if result:
            # Convertir tupla a diccionario
            columns = [desc[0] for desc in cursor.description]
            user = dict(zip(columns, result))
            return user
    conn.close()
    return None

def verify_user_credentials(email: str, password: str) -> dict:
    """Verifica las credenciales de un usuario y retorna el usuario si son correctas"""
    user = get_usuario_by_email(email)
    if user and verify_password(password, user['password']):
        return user
    return None

def save_menu_azca(menu: MenuAzca, usuario_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Insertar menú principal
            cursor.execute("""
                INSERT INTO menus_azca (menu_del_dia, precio, platos, bar_rest, dia, fecha, telefono, aperitivo, usuario_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                menu.menu_del_dia, menu.precio, menu.platos, menu.bar_rest, menu.dia,
                menu.fecha, menu.telefono, menu.aperitivo, usuario_id
            ))
            menu_id = cursor.lastrowid

            # Insertar primeros platos
            if menu.primeros:
                for plato in menu.primeros:
                    cursor.execute("INSERT INTO primeros_platos (menu_id, nombre) VALUES (%s, %s)", (menu_id, plato))

            # Insertar segundos platos
            if menu.segundos:
                for plato in menu.segundos:
                    cursor.execute("INSERT INTO segundos_platos (menu_id, nombre) VALUES (%s, %s)", (menu_id, plato))

            # Insertar complementos
            if menu.complemento:
                for comp in menu.complemento:
                    cursor.execute("INSERT INTO complementos (menu_id, nombre) VALUES (%s, %s)", (menu_id, comp))

            # Insertar postres
            if menu.postre:
                for postre in menu.postre:
                    cursor.execute("INSERT INTO postres (menu_id, nombre) VALUES (%s, %s)", (menu_id, postre))

            # Insertar menús infantiles
            if menu.menu_infantil:
                for inf in menu.menu_infantil:
                    cursor.execute("INSERT INTO menus_infantiles (menu_id, nombre) VALUES (%s, %s)", (menu_id, inf))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_menus_by_usuario(usuario_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Obtener menús del usuario
            cursor.execute("SELECT * FROM menus_azca WHERE usuario_id = %s ORDER BY fecha_creacion DESC", (usuario_id,))
            results = cursor.fetchall()
            
            # Convertir a diccionarios
            columns = [desc[0] for desc in cursor.description]
            menus = [dict(zip(columns, row)) for row in results]

            # Para cada menú, obtener los platos
            for menu in menus:
                menu_id = menu['id']

                # Primeros
                cursor.execute("SELECT nombre FROM primeros_platos WHERE menu_id = %s", (menu_id,))
                primeros = cursor.fetchall()
                menu['primeros'] = [row[0] for row in primeros]

                # Segundos
                cursor.execute("SELECT nombre FROM segundos_platos WHERE menu_id = %s", (menu_id,))
                segundos = cursor.fetchall()
                menu['segundos'] = [row[0] for row in segundos]

                # Complementos
                cursor.execute("SELECT nombre FROM complementos WHERE menu_id = %s", (menu_id,))
                complementos = cursor.fetchall()
                menu['complemento'] = [row[0] for row in complementos]

                # Postres
                cursor.execute("SELECT nombre FROM postres WHERE menu_id = %s", (menu_id,))
                postres = cursor.fetchall()
                menu['postre'] = [row[0] for row in postres]

                # Infantiles
                cursor.execute("SELECT nombre FROM menus_infantiles WHERE menu_id = %s", (menu_id,))
                infantiles = cursor.fetchall()
                menu['menu_infantil'] = [row[0] for row in infantiles]

    finally:
        conn.close()
    return menus

def get_all_menus():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Obtener menús principales
            cursor.execute("""
                SELECT m.*, u.nombre_usuario 
                FROM menus_azca m 
                JOIN usuarios_azca u ON m.usuario_id = u.id 
                ORDER BY m.fecha_creacion DESC
            """)
            results = cursor.fetchall()
            
            # Convertir a diccionarios
            columns = [desc[0] for desc in cursor.description]
            menus = [dict(zip(columns, row)) for row in results]

            # Para cada menú, obtener los platos
            for menu in menus:
                menu_id = menu['id']

                # Primeros
                cursor.execute("SELECT nombre FROM primeros_platos WHERE menu_id = %s", (menu_id,))
                primeros = cursor.fetchall()
                menu['primeros'] = [row[0] for row in primeros]

                # Segundos
                cursor.execute("SELECT nombre FROM segundos_platos WHERE menu_id = %s", (menu_id,))
                segundos = cursor.fetchall()
                menu['segundos'] = [row[0] for row in segundos]

                # Complementos
                cursor.execute("SELECT nombre FROM complementos WHERE menu_id = %s", (menu_id,))
                complementos = cursor.fetchall()
                menu['complemento'] = [row[0] for row in complementos]

                # Postres
                cursor.execute("SELECT nombre FROM postres WHERE menu_id = %s", (menu_id,))
                postres = cursor.fetchall()
                menu['postre'] = [row[0] for row in postres]

                # Infantiles
                cursor.execute("SELECT nombre FROM menus_infantiles WHERE menu_id = %s", (menu_id,))
                infantiles = cursor.fetchall()
                menu['menu_infantil'] = [row[0] for row in infantiles]

    finally:
        conn.close()
    return menus

# Funciones antiguas (mantener compatibilidad)
def save_menu(menu_data: dict):
    # Para compatibilidad, pero usar save_menu_azca en el futuro
    pass

def get_menus():
    return get_all_menus()

# Funciones para ratings/valoraciones
def save_rating(menu_id: int, usuario_id: int, puntuacion: int, resena: str = ""):
    """Guarda una valoración/review para un menú"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO valoraciones (menu_id, usuario_id, puntuacion, resena, fecha_creacion)
                VALUES (%s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE 
                puntuacion = %s, resena = %s, fecha_creacion = NOW()
            """, (menu_id, usuario_id, puntuacion, resena, puntuacion, resena))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error guardando rating: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def get_ratings_by_menu(menu_id: int):
    """Obtiene todas las valoraciones de un menú con información del usuario"""
    conn = get_db_connection()
    ratings = []
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT v.id, u.nombre_usuario, v.puntuacion, v.resena, v.fecha_creacion
                FROM valoraciones v
                JOIN usuarios_azca u ON v.usuario_id = u.id
                WHERE v.menu_id = %s
                ORDER BY v.fecha_creacion DESC
            """, (menu_id,))
            rows = cursor.fetchall()
            for row in rows:
                ratings.append({
                    "id": row[0],
                    "nombre_usuario": row[1],
                    "puntuacion": row[2],
                    "resena": row[3],
                    "fecha": row[4].isoformat() if row[4] else None
                })
    except Exception as e:
        print(f"Error obteniendo ratings: {e}")
    finally:
        conn.close()
    return ratings

def get_average_rating(menu_id: int):
    """Calcula el rating promedio de un menú"""
    conn = get_db_connection()
    average = 0
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT ROUND(AVG(puntuacion), 1) as promedio, COUNT(*) as total
                FROM valoraciones
                WHERE menu_id = %s
            """, (menu_id,))
            row = cursor.fetchone()
            if row and row[0] is not None:
                average = {"promedio": row[0], "total": row[1]}
    except Exception as e:
        print(f"Error calculando rating promedio: {e}")
    finally:
        conn.close()
    return average
