# 📖 Mesa Language v2.2.0 - LA CABRA
## Documentación Completa | Guía de Referencia Bilingüe ES/EN

---

# 📑 ÍNDICE

1.  [Inicio Rápido](#1-inicio-rápido)
2.  [Sintaxis Básica](#2-sintaxis-básica)
3.  [Variables y Tipos](#3-variables-y-tipos)
4.  [Operadores](#4-operadores)
5.  [Control de Flujo](#5-control-de-flujo)
6.  [Funciones](#6-funciones)
7.  [Shapes (Clases)](#7-shapes-clases)
8.  [Colecciones](#8-colecciones)
9.  [Strings](#9-strings)
10. [Entrada/Salida](#10-entradasalida)
11. [📁 Filesystem](#11-filesystem)
12. [🌐 HTTP Client](#12-http-client)
13. [🌐 HTTP Server](#13-http-server)
14. [📋 JSON](#14-json)
15. [🔍 Regex](#15-regex)
16. [🔐 Crypto](#16-crypto)
17. [🗄️ Database](#17-database)
18. [⚡ Concurrencia](#18-concurrencia)
19. [📊 CSV](#19-csv)
20. [🗜️ Compresión](#20-compresión)
21. [📅 DateTime](#21-datetime)
22. [💻 Sistema](#22-sistema)
23. [🔧 Funcional](#23-funcional)
24. [🌐 Web Builder](#24-web-builder)
25. [🏗️ Bajo Nivel](#25-bajo-nivel)
26. [🖥️ x86 Assembler](#26-x86-assembler)
27. [🖥️ MesaOS](#27-mesaos)
28. [🧪 Testing](#28-testing)
29. [Match](#29-match)
30. [Try/Catch](#30-trycatch)
31. [REPL](#31-repl)
32. [Errores y Diagnóstico](#32-errores-y-diagnóstico)
33. [Roadmap](#33-roadmap)

---

# 1. INICIO RÁPIDO

## Instalación

​```bash
git clone <repo>
cd mesa-lang
chmod +x mesa
./mesa version
​```

## Hola Mundo

​```
decir("Hola mundo!")
say("Hello world!")
​```

## Ejecutar

​```bash
./mesa correr archivo.mesa
./mesa run file.mesa
./mesa                     # Modo interactivo REPL
​```

---

# 2. SINTAXIS BÁSICA

## Comentarios

​```
-- Comentario de una línea

/* Comentario
   multilínea */
​```

## Bloques

​```
si verdadero {
    decir("dentro del bloque")
}
​```

## Sin punto y coma

​```
x = 10
y = 20
decir(x + y)
​```

## Interpolación de strings

​```
nombre = "Mesa"
decir("Hola {nombre}!")
​```

---

# 3. VARIABLES Y TIPOS

## Declaración

​```
nombre = "Carlos"
edad = 28
activo = verdadero
precio = 19.99
nulo = nada
​```

## Con tipo explícito

​```
nombre: texto = "Carlos"
edad: entero = 28
precio: decimal = 19.99
​```

## Tipos disponibles

| ES       | EN     | Ejemplo     |
|----------|--------|-------------|
| entero   | int    | 42          |
| decimal  | float  | 3.14        |
| texto    | string | "hola"      |
| booleano | bool   | verdadero   |
| lista    | list   | [1, 2, 3]   |
| mapa     | map    | crear_mapa()|
| nada     | none   | nada        |

---

# 4. OPERADORES

## Aritméticos

​```
5 + 3    -- 8
5 - 3    -- 2
5 * 3    -- 15
10 / 3   -- 3.33
10 % 3   -- 1
2 ** 3   -- 8
​```

## Comparación

​```
== != < > <= >=
​```

## Lógicos

​```
y / and
o / or
no / not
​```

## Asignación compuesta

​```
x += 1
x -= 1
x *= 2
x /= 2
​```

## Rango

​```
0..5    -- [0, 1, 2, 3, 4]
​```

---

# 5. CONTROL DE FLUJO

## Si / If

​```
si edad >= 18 {
    decir("Mayor")
} ademas edad >= 13 {
    decir("Adolescente")
} sino {
    decir("Niño")
}

if age >= 18 {
    say("Adult")
} elif age >= 13 {
    say("Teen")
} else {
    say("Child")
}
​```

## Mientras / While

​```
i = 0
mientras i < 5 {
    decir(i)
    i += 1
}

i = 0
while i < 5 {
    say(i)
    i += 1
}
​```

## Para / For

​```
-- Con lista
para fruta en ["manzana", "banana"] {
    decir(fruta)
}

-- Con índice
para item, idx en ["a", "b", "c"] {
    decir("{idx}: {item}")
}

for fruit in ["apple", "banana"] {
    say(fruit)
}
​```

## Repetir / Repeat

​```
repetir 5 {
    decir("Hola!")
}

repetir 3 como i {
    decir("Iter {i}")
}

repeat 5 { say("Hello!") }
repeat 3 as i { say("{i}") }
​```

## Bucle / Loop (infinito)

​```
bucle {
    decir("Siempre")
    parar
}

loop {
    say("Forever")
    break
}
​```

## Control de bucles

| ES        | EN       | Acción                  |
|-----------|----------|-------------------------|
| parar     | break    | Sale del bucle          |
| continuar | continue | Siguiente iteración     |
| saltar    | skip     | Siguiente iteración     |

---

# 6. FUNCIONES

## Definir

​```
funcion saludar(nombre) {
    decir("Hola {nombre}!")
}

function greet(name) {
    say("Hello {name}!")
}
​```

## Retornar

​```
funcion sumar(a, b) {
    dar a + b
}

function add(a, b) {
    return a + b
}
​```

## Arrow (una línea)

​```
funcion doble(x) -> x * 2
function double(x) -> x * 2
​```

## Lambda

​```
duplicar = funcion(x) -> x * 2
cuadrado = funcion(x) { dar x * x }
​```

---

# 7. SHAPES (CLASES)

​```
forma Persona {
    nombre: texto
    edad: entero

    funcion saludar(yo) {
        decir("Hola soy {yo.nombre}")
    }
}

carlos = Persona { nombre: "Carlos", edad: 28 }
carlos.saludar()
decir(carlos.nombre)
carlos.edad = 29

shape Person {
    name: string
    age: int
    function greet(self) {
        say("Hi I am {self.name}")
    }
}
​```

---

# 8. COLECCIONES

## Listas

​```
nums = [1, 2, 3, 4, 5]
nums.agregar(6)
nums.remover(0)
nums.tamaño()
nums.contiene(3)
nums.invertir()
nums.ordenar()
nums.primero()
nums.último()
nums.unir(", ")
nums.filtrar(funcion(x) -> x > 3)
nums.mapear(funcion(x) -> x * 2)
nums.limpiar()
nums[0]
nums[0] = 99
​```

## Mapas

​```
m = crear_mapa("nombre", "Carlos", "edad", 28)
m.nombre
m.obtener("nombre")
m.claves()
m.valores()
m.contiene("nombre")
m.tamaño()
m.eliminar("edad")
​```

---

# 9. STRINGS

​```
s = "hola mundo"
s.mayusculas()        -- "HOLA MUNDO"
s.minusculas()        -- "hola mundo"
s.dividir(" ")        -- ["hola", "mundo"]
s.recortar()          -- quita espacios
s.reemplazar("o","0") -- "h0la mund0"
s.empieza_con("hola") -- verdadero
s.termina_con("mundo")-- verdadero
s.contiene("la")      -- verdadero
s.encontrar("la")     -- 2
s.tamaño()            -- 10
s.capitalizar()       -- "Hola mundo"
s.titulo()            -- "Hola Mundo"
​```

---

# 10. ENTRADA/SALIDA

​```
decir("Hola")
say("Hello")
imprimir("También")
print("Also")

nombre = preguntar("Tu nombre: ")
name = ask("Your name: ")
​```

## Conversiones

​```
entero("42")     -- 42
decimal("3.14")  -- 3.14
texto(42)        -- "42"
tipo(42)         -- "int"
len("hola")      -- 4
​```

## Matemáticas

​```
abs(-5)          -- 5
min(3, 5)        -- 3
max(3, 5)        -- 5
redondear(3.7)   -- 4
raiz(16)         -- 4
potencia(2, 3)   -- 8
sin(x), cos(x), tan(x)
log(x)
PI               -- 3.14159...
E                -- 2.71828...
suma([1,2,3])    -- 6
rango(5)         -- [0,1,2,3,4]
aleatorio()      -- 0.0 a 1.0
randint(1, 10)
dormir(1)        -- pausar 1 segundo
salir(0)
​```

---

# 11. FILESYSTEM

​```
-- Leer
archivo_leer("datos.txt")
archivo_lineas("datos.txt")
archivo_leer_bytes("img.png")

-- Escribir
archivo_escribir("out.txt", "contenido")
archivo_agregar("log.txt", "nueva línea")
archivo_escribir_bytes("out.bin", [72,101])

-- Verificar
archivo_existe("datos.txt")
es_archivo("datos.txt")
es_directorio("carpeta")
es_legible("datos.txt")
es_escribible("datos.txt")

-- Manipular
archivo_copiar("origen.txt", "copia.txt")
archivo_renombrar("viejo.txt", "nuevo.txt")
archivo_eliminar("temp.txt")
mover("a.txt", "b.txt")

-- Info
archivo_tamaño("datos.txt")
archivo_info("datos.txt")
-- .nombre .ruta .tamaño .extension
-- .es_archivo .es_directorio

-- Directorios
crear_directorio("carpeta")
listar_directorio(".")
listar_todo(".", ".mesa")
directorio_actual()
cambiar_directorio("/ruta")

-- Rutas
ruta_unir("a", "b", "c.txt")
ruta_absoluta("archivo.txt")
ruta_nombre("/home/user/doc.pdf")
ruta_directorio("/home/user/doc.pdf")
ruta_extension("doc.pdf")
ruta_sin_extension("doc.pdf")
​```

### Referencia ES/EN

| ES                 | EN              |
|--------------------|-----------------|
| archivo_leer       | file_read       |
| archivo_escribir   | file_write      |
| archivo_agregar    | file_append     |
| archivo_existe     | file_exists     |
| archivo_eliminar   | file_delete     |
| archivo_copiar     | file_copy       |
| archivo_tamaño     | file_size       |
| archivo_info       | file_info       |
| crear_directorio   | create_dir      |
| listar_directorio  | list_dir        |
| directorio_actual  | cwd             |
| ruta_unir          | path_join       |
| ruta_nombre        | path_name       |

---

# 12. HTTP CLIENT

​```
-- GET
resp = http_get("https://api.com/datos")
decir(resp.status)   -- 200
decir(resp.ok)       -- verdadero
decir(resp.body)     -- contenido

-- POST
datos = crear_mapa("nombre", "Carlos")
resp = http_post("https://api.com/users", datos)

-- PUT
resp = http_put("https://api.com/users/1", datos)

-- DELETE
resp = http_delete("https://api.com/users/1")

-- PATCH
resp = http_patch("https://api.com/users/1", datos)

-- GET con JSON automático
resp = http_json("https://api.com/datos")
si resp.ok {
    decir(resp.datos)
}

-- Descargar archivo
http_descargar("https://url.com/foto.jpg", "foto.jpg")

-- URL encoding
url_codificar("hola mundo")
url_decodificar(encoded)
url_parametros(crear_mapa("q", "mesa"))
​```

### Objeto respuesta

| Campo        | Descripción          |
|--------------|----------------------|
| resp.status  | Código HTTP (200...) |
| resp.ok      | true si 200-299      |
| resp.body    | Cuerpo respuesta     |
| resp.headers | Cabeceras            |

### Referencia ES/EN

| ES              | EN             |
|-----------------|----------------|
| http_get        | http_get       |
| http_post       | http_post      |
| http_put        | http_put       |
| http_delete     | http_delete    |
| http_patch      | http_patch     |
| http_descargar  | http_download  |
| http_json       | fetch_json     |
| url_codificar   | url_encode     |
| url_decodificar | url_decode     |
| url_parametros  | url_params     |

---

# 13. HTTP SERVER

​```
-- Definir rutas
ruta_get("/", funcion(req) {
    dar respuesta_html("<h1>Hola!</h1>")
})

ruta_post("/api/datos", funcion(req) {
    datos = req.body
    dar respuesta_json(crear_mapa("ok", verdadero))
})

ruta_put("/api/datos/:id", funcion(req) {
    id = req.params.id
    dar respuesta_json(crear_mapa("id", id))
})

ruta_delete("/api/datos/:id", funcion(req) {
    dar respuesta_json(crear_mapa("eliminado", verdadero))
})

-- Archivos estáticos
estatico("public")

-- Middleware
middleware(funcion(req) {
    decir("{req.metodo} {req.ruta}")
})

-- Iniciar servidor
escuchar(8080)

-- Servidor async (no bloquea)
servidor_iniciar_async(8080)
​```

## Tipos de respuesta

​```
respuesta_html("<h1>Hola</h1>")
respuesta_html("<h1>Error</h1>", 404)
respuesta_json(crear_mapa("ok", verdadero))
respuesta_json(datos, 201)
respuesta("texto", 200, "text/plain")
redirigir("/nueva-url")
​```

## Objeto request

| Campo        | Descripción           |
|--------------|-----------------------|
| req.method   | GET, POST, etc        |
| req.path     | /ruta/actual          |
| req.params   | Params de ruta (:id)  |
| req.query    | Query string ?k=v     |
| req.body     | Cuerpo JSON parseado  |
| req.headers  | Cabeceras HTTP        |

### Referencia ES/EN

| ES                    | EN                 |
|-----------------------|--------------------|
| ruta_get              | route_get          |
| ruta_post             | route_post         |
| ruta_put              | route_put          |
| ruta_delete           | route_delete       |
| respuesta_html        | response_html      |
| respuesta_json        | response_json      |
| redirigir             | redirect           |
| estatico              | static             |
| escuchar              | listen             |
| servidor_iniciar      | server_start       |
| servidor_detener      | server_stop        |

---

# 14. JSON

​```
-- Parsear
datos = json_parsear('{"nombre": "Ana", "edad": 25}')
decir(datos.nombre)

-- Serializar
obj = crear_mapa("a", 1, "b", 2)
json_texto(obj)
json_bonito(obj)
json_bonito(obj, 4)   -- indent 4

-- Archivos
json_escribir_archivo("config.json", datos)
config = json_leer_archivo("config.json")

-- Validar
json_valido('{"ok": true}')   -- verdadero
json_valido('no es json')     -- falso

-- Acceso por ruta
datos = json_parsear('{"a": {"b": {"c": 99}}}')
json_obtener(datos, "a.b.c")          -- 99
json_obtener(datos, "x.y", "default") -- "default"
json_establecer(datos, "a.b.c", 100)

-- Operaciones
json_merge(a, b)
json_claves(obj)
json_valores(obj)
json_filtrar(obj, ["nombre", "edad"])
json_aplanar(obj_anidado)

-- Crear mapa
m = crear_mapa("clave", "valor", "num", 42)
​```

### Referencia ES/EN

| ES                    | EN                |
|-----------------------|-------------------|
| json_parsear          | json_parse        |
| json_texto            | json_string       |
| json_bonito           | json_pretty       |
| json_leer_archivo     | json_read_file    |
| json_escribir_archivo | json_write_file   |
| json_valido           | json_valid        |
| json_obtener          | json_get          |
| json_establecer       | json_set          |
| json_merge            | json_merge        |
| json_claves           | json_keys         |
| json_valores          | json_values       |
| json_filtrar          | json_filter       |
| json_aplanar          | json_flatten      |
| crear_mapa            | create_map        |

---

# 15. REGEX

​```
-- Buscar primera coincidencia
r = regex_buscar("[0-9]+", "Tengo 25 años")
r.encontrado   -- verdadero
r.valor        -- "25"
r.inicio       -- 6
r.fin          -- 8
r.grupos       -- []

-- Buscar todas
regex_todos("[0-9]+", "3 gatos y 5 perros")  -- ["3","5"]

-- Match desde inicio
regex_coincidir("^[A-Z]", "Hola")

-- Reemplazar
regex_reemplazar("[0-9]+", "X", "abc 123")   -- "abc X"

-- Dividir
regex_dividir("[,;]", "a,b;c")   -- ["a","b","c"]

-- Test booleano
regex_test("[0-9]", "abc123")    -- verdadero

-- Validaciones predefinidas
es_email("user@mail.com")        -- verdadero
es_url("https://mesa.dev")       -- verdadero
es_numero_texto("42.5")          -- verdadero
es_alfanumerico("abc123")        -- verdadero
​```

### Referencia ES/EN

| ES               | EN             |
|------------------|----------------|
| regex_buscar     | regex_search   |
| regex_todos      | regex_all      |
| regex_coincidir  | regex_match    |
| regex_reemplazar | regex_replace  |
| regex_dividir    | regex_split    |
| regex_test       | regex_test     |
| es_email         | is_email       |
| es_url           | is_url         |
| es_numero_texto  | is_numeric     |
| es_alfanumerico  | is_alphanumeric|

---

# 16. CRYPTO

​```
-- Hashing
md5("texto")
sha1("texto")
sha256("texto")
sha512("texto")
hash_hmac("clave", "mensaje", "sha256")
hash_archivo("doc.pdf", "sha256")

-- Base64
base64_codificar("Hola mundo")
base64_decodificar(encoded)

-- Hex
hex_codificar("Hola")
hex_decodificar(hex)

-- UUID y tokens
generar_uuid()          -- "550e8400-..."
generar_token(32)       -- token aleatorio
generar_bytes_aleatorios(16)

-- Passwords seguros
pw = hash_password("mi_contraseña")
pw.hash
pw.salt
verificar_password("mi_contraseña", pw.hash, pw.salt)
​```

### Referencia ES/EN

| ES                       | EN                  |
|--------------------------|---------------------|
| hash_md5 / md5           | md5                 |
| hash_sha256 / sha256     | sha256              |
| hash_hmac                | hmac                |
| hash_archivo             | hash_file           |
| base64_codificar         | base64_encode       |
| base64_decodificar       | base64_decode       |
| hex_codificar            | hex_encode          |
| hex_decodificar          | hex_decode          |
| generar_uuid             | generate_uuid       |
| generar_token            | generate_token      |
| hash_password            | hash_password       |
| verificar_password       | verify_password     |

---

# 17. DATABASE

​```
-- Conectar
db = db_conectar(":memory:")
db = db_conectar("base.db")

-- Crear tabla
db_ejecutar(db, "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")

-- Insertar
db_insertar(db, "users", crear_mapa("name", "Carlos"))

-- Consultar
todos = db_consultar(db, "SELECT * FROM users")
uno = db_consultar_uno(db, "SELECT * FROM users WHERE id = ?", [1])
total = db_contar(db, "users")

-- Actualizar
db_actualizar(db, "users", crear_mapa("name", "Ana"), "id = ?", [1])

-- Eliminar
db_eliminar(db, "users", "id = ?", [1])

-- Info
tablas = db_tablas(db)
cols = db_columnas(db, "users")

-- Transacción
db_transaccion(db, funcion(conn) {
    db_insertar(conn, "users", crear_mapa("name", "A"))
    db_insertar(conn, "users", crear_mapa("name", "B"))
})

-- Cerrar
db_cerrar(db)
​```

### Referencia ES/EN

| ES               | EN            |
|------------------|---------------|
| db_conectar      | db_connect    |
| db_ejecutar      | db_execute    |
| db_consultar     | db_query      |
| db_consultar_uno | db_query_one  |
| db_insertar      | db_insert     |
| db_actualizar    | db_update     |
| db_eliminar      | db_delete     |
| db_contar        | db_count      |
| db_tablas        | db_tables     |
| db_columnas      | db_columns    |
| db_transaccion   | db_transaction|
| db_cerrar        | db_close      |

---

# 18. CONCURRENCIA

​```
-- Crear tarea (hilo)
tarea = tarea_crear(funcion() {
    dormir(2)
    decir("Tarea lista!")
})

-- Esperar resultado
resultado = tarea_esperar(tarea)
tarea_lista(tarea)   -- verdadero/falso

-- Múltiples tareas
t1 = tarea_crear(funcion() -> 1)
t2 = tarea_crear(funcion() -> 2)
resultados = esperar_todas([t1, t2])

-- Paralelo
resultados = paralelo(f1, f2, f3)

-- Canales
canal = canal_crear()
canal_enviar(canal, "hola")
msg = canal_recibir(canal)
canal_vacio(canal)
canal_tamaño(canal)

-- Mutex
m = mutex_crear()
mutex_bloquear(m)
mutex_desbloquear(m)

-- Timers
dormir_ms(500)
temporizador(5, funcion() { decir("Timer!") })
estado = intervalo(2, funcion() { decir("Tick") }, 5)
intervalo_detener(estado)
​```

### Referencia ES/EN

| ES               | EN               |
|------------------|------------------|
| tarea_crear      | task_create      |
| tarea_esperar    | task_wait        |
| tarea_lista      | task_done        |
| esperar_todas    | await_all        |
| paralelo         | parallel         |
| canal_crear      | channel_create   |
| canal_enviar     | channel_send     |
| canal_recibir    | channel_receive  |
| mutex_crear      | mutex_create     |
| mutex_bloquear   | mutex_lock       |
| mutex_desbloquear| mutex_unlock     |
| dormir_ms        | sleep_ms         |
| temporizador     | timer            |
| intervalo        | interval         |

---

# 19. CSV

​```
datos = csv_leer("datos.csv")
csv_escribir("salida.csv", datos)
csv_parsear("nombre,edad\nCarlos,28")
csv_texto(datos)
​```

### Referencia ES/EN

| ES           | EN          |
|--------------|-------------|
| csv_leer     | csv_read    |
| csv_escribir | csv_write   |
| csv_parsear  | csv_parse   |
| csv_texto    | csv_string  |

---

# 20. COMPRESIÓN

​```
comprimido = comprimir("texto largo...")
original = descomprimir(comprimido)

gz = gzip_comprimir("texto")
original = gzip_descomprimir(gz)

comprimir_archivo("grande.txt", "grande.txt.gz")
descomprimir_archivo("grande.txt.gz", "grande.txt")
​```

### Referencia ES/EN

| ES                   | EN                |
|----------------------|-------------------|
| comprimir            | compress          |
| descomprimir         | decompress        |
| gzip_comprimir       | gzip_compress     |
| gzip_descomprimir    | gzip_decompress   |
| comprimir_archivo    | compress_file     |
| descomprimir_archivo | decompress_file   |

---

# 21. DATETIME

​```
ahora()                          -- "2025-01-01T10:30:00"
ahora_utc()                      -- UTC
timestamp()                      -- 1711961400.0
fecha_formato("%d/%m/%Y")        -- "01/01/2025"
dia_semana()                     -- "lunes"

info = fecha_parsear("2025-01-01", "%Y-%m-%d")
info.año
info.mes
info.dia

diff = fecha_diferencia("2025-01-01", "2025-04-01")
diff.dias
diff.horas

manana = fecha_sumar(ahora(), 1)
proxima_hora = fecha_sumar(ahora(), 0, 1)
​```

### Referencia ES/EN

| ES               | EN           |
|------------------|--------------|
| ahora            | now          |
| ahora_utc        | now_utc      |
| timestamp        | timestamp    |
| fecha_formato    | date_format  |
| fecha_parsear    | date_parse   |
| fecha_diferencia | date_diff    |
| fecha_sumar      | date_add     |
| dia_semana       | weekday      |

---

# 22. SISTEMA

​```
-- Ejecutar comandos shell
r = ejecutar_comando("ls -la")
r.salida    -- stdout
r.error     -- stderr
r.codigo    -- exit code
r.ok        -- verdadero si 0

shell("echo hola")
cmd("pwd")

-- Variables de entorno
var_entorno("HOME")
set_var_entorno("MI_VAR", "valor")

-- Info del sistema
plataforma()        -- "linux"
info = info_sistema()
info.pid
info.usuario
info.cwd

-- Argumentos
args = argumentos()

-- Benchmark
r = medir_tiempo(funcion() {
    suma = 0
    repetir 1000000 { suma += 1 }
    dar suma
})
decir("Tiempo: {r.ms} ms")
​```

### Referencia ES/EN

| ES               | EN           |
|------------------|--------------|
| ejecutar_comando | exec_command |
| shell / cmd      | shell / cmd  |
| var_entorno      | env_var      |
| set_var_entorno  | setenv       |
| plataforma       | platform     |
| info_sistema     | system_info  |
| argumentos       | args         |
| medir_tiempo     | benchmark    |

---

# 23. FUNCIONAL

​```
nums = [1, 2, 3, 4, 5]

mapear(funcion(x) -> x * 2, nums)        -- [2,4,6,8,10]
filtrar(funcion(x) -> x % 2 == 0, nums)  -- [2,4]
reducir(funcion(a, b) -> a + b, nums)     -- 15

cada(funcion(x) -> x > 0, nums)          -- verdadero
alguno(funcion(x) -> x > 4, nums)        -- verdadero
encontrar(funcion(x) -> x > 3, nums)     -- 4
encontrar_indice(funcion(x) -> x > 3, nums) -- 3

agrupar(funcion(x) -> x % 2, nums)
zip_listas([1,2,3], ["a","b","c"])        -- [[1,"a"],[2,"b"]]
enumerar([10,20,30])                       -- [[0,10],[1,20]]
aplanar_lista([[1,2],[3,[4,5]]])           -- [1,2,3,4,5]
unico([1,2,2,3,3])                         -- [1,2,3]
partir([1,2,3,4,5,6], 2)                   -- [[1,2],[3,4],[5,6]]
tomar([1,2,3,4,5], 3)                      -- [1,2,3]
saltar_n([1,2,3,4,5], 2)                   -- [3,4,5]
​```

### Referencia ES/EN

| ES               | EN           |
|------------------|--------------|
| mapear           | map_list     |
| filtrar          | filter_list  |
| reducir          | reduce       |
| cada             | every        |
| alguno           | some         |
| encontrar        | find         |
| encontrar_indice | find_index   |
| agrupar          | group_by     |
| zip_listas       | zip          |
| enumerar         | enumerate    |
| aplanar_lista    | flatten      |
| unico            | unique       |
| partir           | chunk        |
| tomar            | take         |
| saltar_n         | drop         |

---

# 24. WEB BUILDER

Crea webs completas sin saber HTML.

## Configuración

​```
pagina("Mi Web", "oceano")
tema("oscuro")
-- Temas: claro, oscuro, oceano, naturaleza, noche
​```

## Elementos

​```
titulo("Grande", 1)
titulo("Medio", 2)
texto("Párrafo normal")
texto("Negrita", "negrita")
texto("Cursiva", "italica")
texto("Centrado", "centro")
imagen("https://url.com/foto.jpg", "alt", 400)
link("Click", "https://url.com")
enlace("Click", "https://url.com", verdadero)
boton("Acción", "/ruta")
boton("Rojo", "/ruta", "#e74c3c")
lista(["Item 1", "Item 2"])
lista(["A", "B"], verdadero)
separador()
espacio(2)
​```

## Contenedores

​```
tarjeta("Título", "Contenido")

tarjeta_inicio("Mi Tarjeta")
    texto("Contenido")
    boton("OK", "/")
tarjeta_fin()

seccion_inicio("Sección")
    texto("Contenido")
seccion_fin()

fila_inicio()
    columna_inicio()
        tarjeta("Col 1", "...")
    columna_fin()
    columna_inicio()
        tarjeta("Col 2", "...")
    columna_fin()
fila_fin()
​```

## Navegación y pie

​```
navbar("Mi Sitio", [["Inicio", "/"], ["About", "/about"]])
footer("© 2025 Mi Sitio")
​```

## Formularios

​```
formulario_inicio("/api/contacto", "POST")
    campo("nombre", "text", "Tu nombre", "Escribe...", verdadero)
    campo("email", "email", "Email", "mail@mail.com")
    campo("msg", "textarea", "Mensaje", "Escribe aquí...")
    boton_enviar("Enviar")
formulario_fin()
​```

## Multimedia y extras

​```
tabla(datos, ["Nombre", "Edad"])
video("https://youtube.com/watch?v=xxx")
audio("https://url.com/audio.mp3")
alerta("Info", "info")
alerta("Éxito!", "exito")
alerta("Cuidado", "aviso")
alerta("Error", "error")
codigo("funcion hola() { decir('hola') }")
cita("La simplicidad es poder", "Da Vinci")
​```

## HTML directo

​```
html("<div class='custom'>HTML directo</div>")
css(".custom { color: red; }")
js("console.log('JS directo');")
​```

## Guardar y servir

​```
web_guardar("mi_pagina.html")
web_servir(8080)
​```

## Templates

​```
web_landing("Título", "Subtítulo", "Botón", "/url")
web_portfolio("Nombre", "Descripción", proyectos)
​```

### Referencia ES/EN

| ES                | EN              |
|-------------------|-----------------|
| pagina            | page            |
| tema              | theme           |
| titulo            | title           |
| texto             | text            |
| imagen            | image           |
| enlace / link     | link            |
| boton             | button          |
| lista             | list            |
| separador         | divider         |
| espacio           | space           |
| tarjeta           | card            |
| tarjeta_inicio    | card_start      |
| tarjeta_fin       | card_end        |
| seccion_inicio    | section_start   |
| seccion_fin       | section_end     |
| fila_inicio       | row_start       |
| fila_fin          | row_end         |
| columna_inicio    | col_start       |
| columna_fin       | col_end         |
| navbar            | navbar          |
| footer            | footer          |
| formulario_inicio | form_start      |
| formulario_fin    | form_end        |
| campo             | field           |
| boton_enviar      | submit          |
| tabla             | table           |
| video             | video           |
| audio             | audio           |
| alerta            | alert           |
| codigo            | code            |
| cita              | quote           |
| html              | html            |
| css               | css             |
| js                | js              |
| web_guardar       | web_save        |
| web_servir        | web_serve       |
| web_landing       | landing         |
| web_portfolio     | portfolio       |

---

# 25. BAJO NIVEL

Acceso directo a memoria real via ctypes.

​```
bajo {
    -- Variables de bajo nivel
    int x = 42
    float pi = 3.14
    char c = 65

    -- Arrays
    int arr[5]
    arr[0] = 10

    -- Punteros y malloc
    int* p = reservar(10, int)
    p[0] = 100
    p[1] = 200
    decir(p[0])
    dir(p)           -- dirección de memoria
    liberar(p)       -- free()

    -- Sizeof
    decir(sizeof(int))    -- 4
    decir(sizeof(double)) -- 8

    -- Memset / Memcpy
    int* a = reservar(5, int)
    llenar(a, 0, 5)              -- memset
    int* b = reservar(5, int)
    copiar_mem(b, a, 5)          -- memcpy
    liberar(a)
    liberar(b)
}
​```

## Tipos disponibles

| Tipo   | Bytes | Descripción    |
|--------|-------|----------------|
| int    | 4     | Entero 32 bits |
| float  | 4     | Float 32 bits  |
| double | 8     | Float 64 bits  |
| char   | 1     | Carácter       |
| byte   | 1     | Byte           |
| long   | 8     | Entero 64 bits |
| short  | 2     | Entero 16 bits |

---

# 26. x86 ASSEMBLER

Mesa incluye un ensamblador x86 real integrado.
Genera bytecode x86 ejecutable sin C ni NASM.

## Crear ensamblador

​```
asm = x86_nuevo()
​```

## Instrucciones disponibles

​```
-- Setup boot
iniciar_boot(asm)          -- CLI + XOR + MOV segs + STI
modo_video(asm, 0x03)      -- INT 10h modo 80x25
limpiar_pantalla(asm)      -- INT 10h scroll
mover_cursor(asm, fila, col) -- INT 10h cursor

-- Labels
etiqueta(asm, "mi_label")

-- Jumps y calls
llamar(asm, "funcion")     -- CALL near
jmp_a(asm, "label")        -- JMP short
si_igual(asm, "label")     -- JE short
si_distinto(asm, "label")  -- JNE short

-- MOV registros
mov_ah(asm, 0x0E)
mov_al(asm, 65)
mov_ax(asm, 0x0600)
mov_bx(asm, 0x0007)
mov_si(asm, 0x7C60)

-- Stack
push_ax(asm)
pop_ax(asm)
push_bx(asm)
pop_bx(asm)

-- Comparar
cmp_al(asm, 104)           -- CMP AL, 'h'

-- BIOS
int_asm(asm, 0x10)         -- INT 10h (video)
int_asm(asm, 0x16)         -- INT 16h (teclado)
int_asm(asm, 0x19)         -- INT 19h (reboot)
reiniciar(asm)             -- INT 19h

-- Misc
hlt(asm)                   -- HLT
nop(asm)                   -- NOP
ret_asm(asm)               -- RET
lodsb(asm)                 -- LODSB

-- Bytes raw
x86_bytes(asm, [0xB4, 0x0E, 0xCD, 0x10])

-- Strings
cadena(asm, "nombre", "texto del string\r\n")

-- Funciones BIOS predefinidas
insertar_print_str(asm)    -- función print_str completa
insertar_print_char(asm)   -- función print_char
insertar_read_key(asm)     -- función read_key

-- Apuntar SI a string
apuntar(asm, 0x7C00, "nombre_string")

-- Compilar
codigo = compilar(asm)

-- Info
x86_pos(asm)               -- posición actual en bytes
x86_tamaño(asm)            -- tamaño total
offset_de(asm, "label")    -- offset de un label
​```

## Crear imagen booteable

​```
-- Empaquetar en bootsector (512 bytes + firma 0x55 0xAA)
boot = bootsector(codigo)

-- Crear imagen de disco (1.44 MB)
crear_imagen(boot, "os.img", 1440)

-- También puedes escribir directamente
crear_directorio("mesa-os")
archivo_escribir_bytes("mesa-os/os.img", boot)

-- Lanzar QEMU
lanzar_qemu("mesa-os/os.img")
​```

### Referencia ES/EN

| ES                    | EN                     |
|-----------------------|------------------------|
| x86_nuevo             | x86_new                |
| etiqueta              | label                  |
| llamar                | call (x86_call)        |
| jmp_a                 | jmp (x86_jmp)          |
| si_igual              | je (x86_je)            |
| si_distinto           | jne (x86_jne)          |
| apuntar               | si_label               |
| cadena                | x86_string             |
| compilar              | x86_resolver           |
| iniciar_boot          | setup_boot             |
| limpiar_pantalla      | bios_clear_screen      |
| mover_cursor          | bios_cursor            |
| modo_video            | bios_set_video         |
| insertar_print_str    | bios_funcion_print_str |
| insertar_print_char   | bios_funcion_print_char|
| insertar_read_key     | bios_funcion_read_key  |
| reiniciar             | bios_reboot            |
| bootsector            | bootsector             |
| crear_imagen          | create_disk            |
| lanzar_qemu           | boot (qemu)            |

---

# 27. MESAOS

## Plantilla base (con escritura de teclado)

​```
-- mi_os.mesa - Plantilla MesaOS
LOAD_ADDR = 0x7C00
IMAGEN = "mesa-os/mi_os.img"
CERO = 0

-- Strings (cortos para caber en 510 bytes)
bienvenida = "\r\n Mi OS con Mesa!\r\n Escribe algo:\r\n"
prompt = "\r\n> "

asm = x86_nuevo()
iniciar_boot(asm)
modo_video(asm, 0x03)
limpiar_pantalla(asm)
mover_cursor(asm, CERO, CERO)

-- Mostrar bienvenida
apuntar(asm, LOAD_ADDR, "bienvenida")
llamar(asm, "print_str")

-- Prompt
etiqueta(asm, "prompt")
apuntar(asm, LOAD_ADDR, "prompt")
llamar(asm, "print_str")

-- Loop lectura
etiqueta(asm, "leer")
llamar(asm, "read_key")

-- Enter → nueva línea
cmp_al(asm, 13)
si_igual(asm, "enter")

-- Backspace → borrar
cmp_al(asm, 8)
si_igual(asm, "borrar")

-- Mostrar tecla
push_ax(asm)
llamar(asm, "print_char")
pop_ax(asm)
jmp_a(asm, "leer")

-- Enter: CR + LF + nuevo prompt
etiqueta(asm, "enter")
x86_bytes(asm, [0xB4, 0x0E, 0xB0, 0x0D, 0xBB, 0x07, 0x00, 0xCD, 0x10])
x86_bytes(asm, [0xB0, 0x0A, 0xCD, 0x10])
jmp_a(asm, "prompt")

-- Backspace: borrar carácter
etiqueta(asm, "borrar")
x86_bytes(asm, [0xB4, 0x0E, 0xB0, 0x08, 0xBB, 0x07, 0x00, 0xCD, 0x10])
x86_bytes(asm, [0xB0, 0x20, 0xCD, 0x10])
x86_bytes(asm, [0xB0, 0x08, 0xCD, 0x10])
jmp_a(asm, "leer")

-- HLT fallback
etiqueta(asm, "fin")
hlt(asm)
jmp_a(asm, "fin")

-- Funciones BIOS
insertar_print_str(asm)
insertar_print_char(asm)
insertar_read_key(asm)

-- Strings (siempre al final)
cadena(asm, "bienvenida", bienvenida)
cadena(asm, "prompt", prompt)

-- Compilar y lanzar
codigo = compilar(asm)
tam = len(codigo)
decir("Kernel: {tam} bytes")

si tam > 510 {
    decir("Error: demasiado grande. Acorta los strings.")
    salir(1)
}

boot = bootsector(codigo)
crear_directorio("mesa-os")
archivo_escribir_bytes(IMAGEN, boot)
decir("Imagen: {IMAGEN}")
lanzar_qemu(IMAGEN)
​```

## Ejecutar

​```bash
./mesa correr mesa-os/mi_os.mesa
​```

## Reglas importantes

| Regla | Motivo |
|-------|--------|
| Strings cortos | Máximo 510 bytes en total |
| `jmp_a` en vez de `saltar` | `saltar` es keyword de Mesa |
| Strings siempre al final | Después de las funciones BIOS |
| `insertar_*` antes de `cadena` | Las funciones van antes de los datos |
| `CERO = 0` para args numéricos | Evita problemas del parser con literales |

---

# 28. TESTING

​```
prueba "suma correcta" {
    verificar(2 + 2 == 4)
    verificar(10 + 5 == 15, "Suma incorrecta")
}

prueba "strings" {
    nombre = "Mesa"
    verificar(len(nombre) == 4)
    verificar(nombre == "Mesa")
}

test "addition" {
    check(2 + 2 == 4)
    assert(10 + 5 == 15)
}
​```

​```bash
./mesa correr tests.mesa
# Output:
# 🧪 Ejecutando tests...
#   ✅ suma correcta
#   ✅ strings
# 📊 Resultados: 2/2 pasaron
​```

---

# 29. MATCH

​```
coincidir valor {
    1 -> decir("uno")
    2 -> decir("dos")
    _ -> decir("otro")
}

coincidir cmd {
    "salir" -> {
        decir("Adiós!")
        salir(0)
    }
    "ayuda" -> decir("Comandos: salir, ayuda")
    _ -> decir("Desconocido")
}

match value {
    1 -> say("one")
    _ -> say("other")
}
​```

---

# 30. TRY/CATCH

​```
intentar {
    resultado = 10 / 0
} capturar error {
    decir("Error: {error}")
} finalmente {
    decir("Siempre se ejecuta")
}

try {
    result = 10 / 0
} catch error {
    say("Error: {error}")
} finally {
    say("Always runs")
}

-- Lanzar errores
funcion dividir(a, b) {
    si b == 0 {
        lanzar "División por cero"
    }
    dar a / b
}
​```

---

# 31. REPL

​```bash
./mesa
# 🏓 Mesa Language v2.2.0
# mesa> 2 + 2
# 4
# mesa> nombre = "Mesa"
# mesa> decir("Hola {nombre}")
# Hola Mesa
# mesa> salir
​```

---

# 32. ERRORES Y DIAGNÓSTICO

Mesa detecta errores con línea, columna y descripción:

​```
❌ Error de sintaxis en L15:C26: Token inesperado: NEWLINE
❌ Error linea 3, col 5: Caracter inesperado '@'
❌ Error: Variable 'x' no definida
​```

## Tipos de error

| Error | Cuándo ocurre |
|-------|---------------|
| LexerError | Carácter inválido en el código |
| ParseError | Sintaxis incorrecta |
| MesaRuntimeError | Error en tiempo de ejecución |

## Debug mode

​```bash
./mesa correr archivo.mesa --debug
# Muestra tokens y AST completo
​```

---

# 33. ROADMAP

​```
v2.2.0  ✅ ACTUAL
        - HTTP Client + Server
        - JSON, Regex, Crypto
        - SQLite integrado
        - Concurrencia (hilos, canales)
        - CSV, Compresión, DateTime
        - Web Builder (HTML sin HTML)
        - x86 Assembler integrado
        - MesaOS (bootea en QEMU)
        - 190+ funciones bilingües
        - Detector de errores con línea

v2.3.0  📋 PRÓXIMO
        - Package manager (mesa instalar xxx)
        - Módulos de terceros
        - mesa nuevo proyecto (scaffolding)
        - Más temas para Web Builder

v2.4.0  📋 PLANIFICADO
        - Tipos opcionales avanzados
        - Debugger paso a paso
        - Profiler integrado
        - Más validaciones en tiempo real

v3.0.0  🎯 FUTURO
        - Compilador a binario nativo (via LLVM)
        - Velocidad comparable a Go/Rust
        - Tipado estático opcional completo

v3.1.0  🎯 FUTURO
        - Mesa → WebAssembly
        - Corre en el navegador
        - Mesa en el frontend

v4.0.0  🚀 VISIÓN
        - Runtime propio en Rust
        - Velocidad máxima
        - Sin dependencia de Python
        - Mesa autocompilado (bootstrapping)
​```

---

# CHEATSHEET RÁPIDO

​```
-- Variables
x = 42
nombre = "Mesa"
activo = verdadero
nums = [1, 2, 3]
m = crear_mapa("a", 1, "b", 2)

-- Funciones
funcion f(a, b) { dar a + b }
cuadrado = funcion(x) -> x * x

-- Control
si x > 0 { decir("positivo") }
mientras x > 0 { x -= 1 }
para i en 0..10 { decir(i) }
repetir 5 como i { decir(i) }

-- Shapes
forma Animal {
    nombre: texto
    funcion hablar(yo) { decir(yo.nombre) }
}
gato = Animal { nombre: "Michi" }
gato.hablar()

-- IO
decir("Hola!")
nombre = preguntar("Tu nombre: ")

-- Archivos
archivo_escribir("datos.txt", "Hola")
contenido = archivo_leer("datos.txt")

-- JSON
obj = crear_mapa("a", 1, "b", 2)
json_texto(obj)
json_parsear('{"x": 42}')
json_obtener(datos, "a.b.c")

-- HTTP
resp = http_get("https://api.com")
resp = http_post("https://api.com", datos)

-- Server
ruta_get("/", funcion(req) -> respuesta_html("<h1>Hola</h1>"))
escuchar(8080)

-- Web Builder
pagina("Mi Web", "oscuro")
titulo("Hola!")
texto("Bienvenido")
web_servir(8080)

-- Database
db = db_conectar(":memory:")
db_ejecutar(db, "CREATE TABLE t (id INTEGER PRIMARY KEY, x TEXT)")
db_insertar(db, "t", crear_mapa("x", "hola"))
db_consultar(db, "SELECT * FROM t")

-- Regex
es_email("user@mail.com")
regex_buscar("[0-9]+", "abc123")

-- Crypto
sha256("texto")
token = generar_token(32)
uuid = generar_uuid()

-- OS (x86 real)
asm = x86_nuevo()
iniciar_boot(asm)
limpiar_pantalla(asm)
cadena(asm, "msg", "\r\n Hola desde x86!\r\n")
apuntar(asm, 0x7C00, "msg")
llamar(asm, "print_str")
insertar_print_str(asm)
boot = bootsector(compilar(asm))
archivo_escribir_bytes("os.img", boot)
lanzar_qemu("os.img")

-- Testing
prueba "test" { verificar(1 + 1 == 2) }
​```

---

© Mesa Language v2.2.0 - LA CABRA 🐐
Primer lenguaje bilingüe ES/EN del mundo.
Con OS real. Con stdlib completa. Sin imports.