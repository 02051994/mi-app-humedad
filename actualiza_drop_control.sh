#!/bin/bash

echo "Ejecutando script: $(date)"

# Ir al directorio del proyecto
cd /mnt/c/Users/PC/mi-app-humedad || {
    echo "Error: no se pudo acceder a la carpeta del proyecto"
    exit 1
}

# Ejecutar el script Python usando el Python de Windows
/mnt/c/Users/PC/AppData/Local/Programs/Python/Python313/python.exe datos_drop_control.py

# Git: agregar, commitear y pushear si hay cambios
if [[ -n $(git status --porcelain) ]]; then
    echo "[INFO] Cambios detectados. Haciendo push..."
    git add .
    git commit -m "Actualización automática desde WSL"
    git push
else
    echo "[INFO] No hay cambios para commitear."
fi

# Escribir en log
echo "[INFO] Script ejecutado correctamente a las $(date)" >> log_auto.txt
