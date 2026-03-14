document.addEventListener('DOMContentLoaded', () => {
    
    // 1. MODAL DE ACCESO
    const authModal = document.getElementById('authModal');
    const headerLoginBtn = document.getElementById('headerLoginBtn');
    const heroSignupBtn = document.getElementById('heroSignupBtn'); 
    const closeModal = document.getElementById('closeModal');
    
    const loginTab = document.getElementById('loginTab');
    const signupTab = document.getElementById('signupTab');
    const loginForm = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');

    const openModal = (tab = 'login') => {
        if (!authModal) return; 
        authModal.style.display = 'flex';
        // Animación suave al abrir
        authModal.style.opacity = '0';
        setTimeout(() => { authModal.style.opacity = '1'; authModal.style.transition = 'opacity 0.3s ease'; }, 10);
        
        if (tab === 'signup') activateSignup();
        else activateLogin();
    };

    const closeModalFunc = () => {
        if (authModal) {
            authModal.style.opacity = '0';
            setTimeout(() => { authModal.style.display = 'none'; }, 300);
        }
    };

    const activateLogin = () => {
        loginTab.classList.add('active');
        signupTab.classList.remove('active');
        loginForm.classList.add('active');
        signupForm.classList.remove('active');
    };

    const activateSignup = () => {
        signupTab.classList.add('active');
        loginTab.classList.remove('active');
        signupForm.classList.add('active');
        loginForm.classList.remove('active');
    };

    if (headerLoginBtn) headerLoginBtn.addEventListener('click', () => openModal('login'));
    if (heroSignupBtn) heroSignupBtn.addEventListener('click', () => openModal('signup'));
    if (closeModal) closeModal.addEventListener('click', closeModalFunc);
    
    if (loginTab) loginTab.addEventListener('click', activateLogin);
    if (signupTab) signupTab.addEventListener('click', activateSignup);

    if (authModal) {
        authModal.addEventListener('click', (e) => {
            if (e.target === authModal) closeModalFunc();
        });
    }

    // 2. REDIRECCIÓN EN LA DEMO
    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault(); 
            window.location.href = 'dashboard-cliente.html';
        });
    }

    if (signupForm) {
        signupForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const rolSeleccionado = document.getElementById('signupRole').value;
            if (rolSeleccionado === 'Cliente') {
                window.location.href = 'dashboard-cliente.html';
            } else if (rolSeleccionado === 'Restaurante') {
                window.location.href = 'dashboard-restaurante.html';
            }
        });
    }

    // 3. SIMULACIÓN DE IA (DASHBOARD RESTAURANTE)
    const menuInput = document.getElementById('menuInput');
    if (menuInput) {
        menuInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const precioInput = document.getElementById('ia-precio');
                const primerosInput = document.getElementById('ia-primeros');
                const segundosInput = document.getElementById('ia-segundos');

                precioInput.value = "Analizando con Azure AI...";
                primerosInput.value = "Extrayendo texto...";
                segundosInput.value = "Extrayendo texto...";

                setTimeout(() => {
                    precioInput.value = "13.50€";
                    primerosInput.value = "- Salmorejo cordobés\n- Ensalada de cabra\n- Risotto trufado";
                    segundosInput.value = "- Entrecot a la parrilla\n- Lomo de salmón\n- Secreto ibérico";
                    alert("¡Éxito! Azure Document Intelligence ha procesado el menú.");
                }, 2500);
            }
        });
    }
});