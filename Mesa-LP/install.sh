#!/bin/bash
# ============================================================================
# Mesa Language - INSTALADOR DE RESCATE
# ============================================================================

# 1. Definir la ruta de forma manual y segura
MESA_DIR="/home/$USER/.mesa"
MESA_BIN="$MESA_DIR/bin"
REPO_ORIGEN=$(pwd)

echo "Instalando Mesa en $MESA_DIR..."

# 2. Crear carpetas (sin sudo para que sean TUYAS)
mkdir -p "$MESA_DIR"
mkdir -p "$MESA_BIN"

# 3. Copiar los archivos del lenguaje
echo "Copiando archivos..."
cp -r "$REPO_ORIGEN"/* "$MESA_DIR/"

# 4. Crear el lanzador (el que busca Bash)
echo "Creando lanzador..."
cat <<EOF > "$MESA_BIN/mesa"
#!/bin/bash
python3 "$MESA_DIR/mesa" "\$@"
EOF

# 5. Dar permisos de ejecución
chmod +x "$MESA_BIN/mesa"
chmod +x "$MESA_DIR/mesa"

# 6. Crear el acceso global (AQUÍ SÍ USAMOS SUDO)
echo "Configurando comando global..."
sudo ln -sf "$MESA_BIN/mesa" /usr/local/bin/mesa

# 7. Limpiar la memoria de comandos de la terminal
hash -r

echo "------------------------------------------------"
echo "✅ ¡INSTALACIÓN COMPLETADA!"
echo "Escribe: mesa version"
echo "------------------------------------------------"