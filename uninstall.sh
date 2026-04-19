#!/bin/bash
# ============================================================================
# Mesa Language - DESINSTALADOR FORZOSO (Hardcoded)
# ============================================================================

# 1. Definimos la ruta exacta que queremos eliminar
TARGET_DIR="/home/$USER/.mesa"
GLOBAL_BIN="/usr/local/bin/mesa"

echo "⚠️  Iniciando desinstalación forzosa de Mesa..."

# 2. Borrar la carpeta con privilegios máximos
# Usamos sudo para asegurar que incluso archivos de root se borren
if [ -d "$TARGET_DIR" ]; then
    echo "Eliminando carpeta $TARGET_DIR..."
    sudo rm -rf "$TARGET_DIR"
else
    echo "La carpeta $TARGET_DIR ya no existe."
fi

# 3. Eliminar el comando global
if [ -L "$GLOBAL_BIN" ] || [ -f "$GLOBAL_BIN" ]; then
    echo "Eliminando acceso global en $GLOBAL_BIN..."
    sudo rm -f "$GLOBAL_BIN"
fi

# 4. Limpiar la caché de la terminal
hash -r

echo -e "\n✅ Mesa ha sido ELIMINADO completamente."