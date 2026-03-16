// Cliente API para conectar con el backend FastAPI
const API_BASE_URL = 'http://localhost:8000'; // Cambia según tu configuración

let authToken = localStorage.getItem('authToken');

// Funciones de autenticación
async function registerUser(userData) {
    try {
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(userData)
        });
        if (!response.ok) throw new Error('Error en registro');
        return await response.json();
    } catch (error) {
        console.error('Error:', error);
        return null;
    }
}

async function loginUser(credentials) {
    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(credentials)
        });
        if (!response.ok) throw new Error('Error en login');
        const data = await response.json();
        authToken = data.access_token;
        localStorage.setItem('authToken', authToken);
        localStorage.setItem('userInfo', JSON.stringify(data.user));
        return data;
    } catch (error) {
        console.error('Error:', error);
        return null;
    }
}

async function fetchMenus() {
    try {
        const response = await fetch(`${API_BASE_URL}/menus`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        if (!response.ok) throw new Error('Error al obtener menús');
        return await response.json();
    } catch (error) {
        console.error('Error:', error);
        return [];
    }
}

async function uploadMenuImage(imageFile) {
    const formData = new FormData();
    formData.append('file', imageFile);

    try {
        const response = await fetch(`${API_BASE_URL}/predict-menu`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            body: formData
        });
        if (!response.ok) throw new Error('Error al procesar imagen');
        return await response.json();
    } catch (error) {
        console.error('Error:', error);
        return null;
    }
}

async function saveMenu(menuData) {
    try {
        const response = await fetch(`${API_BASE_URL}/menus`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(menuData)
        });
        if (!response.ok) throw new Error('Error al guardar menú');
        return await response.json();
    } catch (error) {
        console.error('Error:', error);
        return null;
    }
}

function logout() {
    authToken = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('userInfo');
}

// Función para inicializar la app
async function initApp() {
    // Ejemplo: cargar menús al inicio si hay token
    if (authToken) {
        const menus = await fetchMenus();
        console.log('Menús cargados:', menus);
    }
}

// Llamar a init cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', initApp);