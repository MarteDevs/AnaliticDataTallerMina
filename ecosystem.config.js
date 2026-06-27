module.exports = {
  apps: [
    {
      name: "analisis-data-taller",
      script: "wsgi.py",
      interpreter: "./.venv/bin/python", // Usa el python nativo de tu entorno virtual
      cwd: "/var/www/AnaliticDataTallerMina", // Directorio en tu VPS
      watch: false,
      max_memory_restart: "1G",
      autorestart: true,
      restart_delay: 3000,
      env: {
        FLASK_ENV: "production"
      }
    }
  ]
};
