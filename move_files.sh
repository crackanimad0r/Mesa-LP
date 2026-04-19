#!/bin/bash

echo "📦 Moviendo archivos de src/ a compiler/..."

# Mover archivos
mv src/lexer.py compiler/ 2>/dev/null && echo "  ✅ lexer.py movido"
mv src/parser.py compiler/ 2>/dev/null && echo "  ✅ parser.py movido"
mv src/ast_nodes.py compiler/ 2>/dev/null && echo "  ✅ ast_nodes.py movido"
mv src/interpreter.py compiler/ 2>/dev/null && echo "  ✅ interpreter.py movido"

# Remover directorio src si está vacío
if [ -d "src" ] && [ -z "$(ls -A src)" ]; then
    rmdir src
    echo "  🗑️  Directorio src/ removido (vacío)"
fi

echo "✅ Archivos movidos correctamente"

# Verificar estructura
echo ""
echo "📁 Archivos en compiler/:"
ls -1 compiler/

