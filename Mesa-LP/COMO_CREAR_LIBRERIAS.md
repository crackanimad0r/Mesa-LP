# 📦 Construyendo y Publicando Librerías en Mesa

Mesa Lang v4.0.0 NATIVO introdujo un ecosistema soberano basado en Rust que te permite compartir tu código con una velocidad y estabilidad sin precedentes. ¡Aquí tienes la guía definitiva!

## 1. Crear una Nueva Librería

Nunca empieces de cero. Usa nuestra herramienta oficial de _scaffolding_:

```bash
./mesa nuevo libreria mi_super_lib
```

Esto generará automáticamente una carpeta `mi_super_lib/` con la estructura perfecta:
- `mi_super_lib.mesa`: El código fuente principal de tu librería.
- `mesa_pkg.json`: El manifiesto que contiene el nombre, autor, versión y descripción.
- `tests/test_mi_super_lib.mesa`: Un entorno preconfigurado para escribir pruebas (TDD).
- `README.md`: Documentación inicial para tus usuarios.

## 2. Escribir el Código

Aprovecha el nuevo motor **nativo** de Mesa. Usa funciones de flecha para un código más limpio y moderno.

**Ejemplos de funciones exportadas:**
```mesa
-- Dentro de mi_super_lib.mesa (Sintaxis v4.0.0)

-- Función clásica
funcion saludar(nombre) {
    decir("Meeeee~ Hola " + nombre + " 🐐")
}

-- Función de flecha (Arrow function)
suma = (a, b) -> a + b

-- Manipulación nativa de listas
recortar = (lista) -> lista[1..-1]
```

## 3. Hacer Pruebas (Test-Driven Development)

Es importante asegurar la calidad de tu código. Escribe tus pruebas dentro de la carpeta `tests/`.

```bash
mesa correr tests/test_mi_super_lib.mesa
```

## 4. Publicar tu Librería 🚀

Una vez que tu código esté listo, es hora de publicarlo en el **Registro Oficial de Mesa**.
Si tienes `Firebase Hosting` configurado y quieres publicar para todo el mundo, navega al directorio de tu librería y usa el flag `--web` mágico:

```bash
cd mi_super_lib
mesa publicar . --web
```

¿Qué hace esto por ti?
1. Comprime tu código de manera segura.
2. Actualiza la página web pública del Registro Oficial.
3. Despliega la web automáticamente en servidor global.

## 5. ¡Instalar y Disfrutar!

Cualquier persona en el mundo ahora puede importar tu código usando el link generado por la web pública:

```bash
mesa instalar mi_super_lib --url https://<TU-DOMINIO>.web.app/mi_super_lib.zip
```

Y en el código, simplemente se usa:
```mesa
usar "mi_super_lib"

saludar("Mundo")
```

¡Bienvenido al ecosistema moderno de Mesa Lang! 🐐
