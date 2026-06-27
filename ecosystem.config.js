module.exports = {
  apps: [
    {
      name: "analisis-data-taller",
      // En Linux, ejecutamos gunicorn directamente desde el entorno virtual local para mantener el aislamiento
      script: "./.venv/bin/gunicorn",
      // Si el VPS es Windows, se cambiaría a:
      // script: "app.py",
      // interpreter: "./.venv/Scripts/python.exe",
      
      // Argumentos para Gunicorn en Linux:
      // -w 4: Utiliza 4 procesos de trabajo (workers) para atender peticiones concurrentes
      // -b 0.0.0.0:5000: Escucha en todas las interfaces de red en el puerto 5000
      // --timeout 120: Timeout de 2 minutos para evitar cortes en la generación de PDFs consolidados pesados
      args: "-w 4 -b 0.0.0.0:5000 app:app --timeout 120",
      
      cwd: "/var/www/AnalisisData", // Ruta del proyecto en el VPS (ajústala según la ubicación real)
      watch: false,
      max_memory_restart: "1G", // Reinicia el proceso automáticamente si consume más de 1GB
      autorestart: true,
      restart_delay: 3000, // Espera 3 segundos antes de reiniciar tras un fallo
      env: {
        FLASK_ENV: "production"
      }
    }
  ]
};
