// Funcionalidad para navegación lateral
function showSection(section) {
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    if (section === 'inicio') document.querySelectorAll('.nav-btn')[0].classList.add('active');
    if (section === 'nulos') document.querySelectorAll('.nav-btn')[1].classList.add('active');
    if (section === 'estadisticas') document.querySelectorAll('.nav-btn')[2].classList.add('active');
    if (section === 'otras') document.querySelectorAll('.nav-btn')[3].classList.add('active');

    document.getElementById('section-inicio').style.display = (section === 'inicio') ? 'block' : 'none';
    document.getElementById('section-nulos').style.display = (section === 'nulos') ? 'block' : 'none';
    document.getElementById('section-estadisticas').style.display = (section === 'estadisticas') ? 'block' : 'none';
    document.getElementById('section-otras').style.display = (section === 'otras') ? 'block' : 'none';
}

// Manejador de subida de archivo (ejemplo, debes adaptar la URL a tu backend)
document.getElementById('upload-form').addEventListener('submit', function(e){
    e.preventDefault();
    let formData = new FormData(this);
    fetch('/ruta/a/tu/upload/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': window.CSRF_TOKEN || ''
        }
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('upload-status').innerText = "CSV cargado correctamente.";
        // Llama a funciones para renderizar los gráficos con los datos recibidos
        // renderNulosChart(data.nulos);
        // renderEstadisticasChart(data.estadisticas);
    })
    .catch(error => {
        document.getElementById('upload-status').innerText = "Error al cargar el archivo.";
    });
});

// Ejemplo de función para renderizar gráficos (debes implementar con tus datos)
function renderNulosChart(datos) {
    const ctx = document.getElementById('nulosChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: datos.columnas,
            datasets: [{
                label: 'Valores Nulos',
                data: datos.valores,
                backgroundColor: '#176ee5'
            }]
        }
    });
}