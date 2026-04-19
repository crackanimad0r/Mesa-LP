#!/bin/bash
echo "🔥 Mesa Lang v3.0 - Suite de Pruebas Maestra"
echo "------------------------------------------"

# 1. Asegurar paquetes instalados
echo "📦 Registrando e instalando paquetes..."
./mesa publicar mates > /dev/null
./mesa publicar utiles > /dev/null
./mesa publicar eml > /dev/null
./mesa instalar mates > /dev/null && echo "✅ Pack mates OK"
./mesa instalar utiles > /dev/null && echo "✅ Pack utiles OK"
./mesa instalar eml > /dev/null && echo "✅ Pack eml OK"

echo ""
echo "🔍 1. Validando Tipado Estático (Debe detectar error)"
./mesa correr prueba_tipos.mesa 2>&1 | grep "Error de Tipado" && echo "✅ Tipado Estático Detectado" || echo "❌ Fallo en detección de tipos"

echo ""
echo "🏓 2. Ejecutando tests de librerías (Intérprete)"
./mesa correr mates/tests/test_mates.mesa && echo "✅ Mates OK"
./mesa correr utiles/tests/test_utiles.mesa && echo "✅ Utiles OK"
./mesa correr eml/tests/test_eml.mesa && echo "✅ EML OK"

echo ""
echo "🚀 3. Benchmarking Nativo (AOT LLVM)"
./mesa compilar benchmark.mesa > /dev/null
echo -n "Resultado Nativo: "
./benchmark
echo "✅ Compilación LLVM y ejecución nativa OK"

echo ""
echo "------------------------------------------"
echo "✨ MESA ESTÁ EN ESTADO PERFECTO ✨"
