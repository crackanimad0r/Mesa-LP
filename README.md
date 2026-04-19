<img width="1920" height="1080" alt="MESA-LP" src="https://github.com/user-attachments/assets/1e748962-8a07-46b2-8960-3bba8a441656" />

# 🐐 Mesa Language v4.0.0 — NATIVO (EL SALTO FINAL)

**Mesa** es un lenguaje de programación bilingüe y soberano diseñado para romper las barreras entre el desarrollo de alto nivel y la ingeniería de sistemas. Tras alcanzar la **v4.0.0**, Mesa ha completado su transición a un motor **100% nativo en Rust**, eliminando por completo la dependencia de Python y ofreciendo una velocidad y estabilidad sin precedentes.

---

## 🚀 ¿Por qué Mesa?

* **Soberanía Total:** +200 funciones nativas integradas. Olvídate de `npm install` o `pip install`. HTTP (Síncrono/Asíncrono), Criptografía, Bases de Datos y JSON vienen de serie.
* **Bilingüe por Diseño:** Programa en Español o Inglés sin alias ni parches. `decir()` es tan potente como `say()`. Paridad total en cada línea.
* **De la Web al Hierro:** Escribe una aplicación web completa con servidores reales en 20 líneas o baja al nivel de los registros x86 para crear tu propio OS con el toolkit nativo.
* **Motor Nativo (Rust):** Adiós al bytecode interpretado de Python. Mesa ahora corre directamente sobre un runtime de alto rendimiento escrito en Rust.

---

## 🎨 Alto Nivel: Web Builder con Servidor Real
Mesa elimina la frustración del desarrollo web. No más etiquetas infinitas ni simulaciones, solo lógica pura y **servidores HTTP nativos (`TcpListener`)**.

```mesa
-- Una web profesional en segundos (mi_web.mesa)
pagina("Mesa World", "oscuro")

navbar("Mesa", [["Inicio", "/"], ["Docs", "/docs"]])

titulo("Bienvenido al Futuro")
texto("Crea webs potentes con servidores reales sin escribir ni una línea de HTML.")

tarjeta("Soberanía", "Mesa no depende de librerías externas.")
alerta("Mesa es LA CABRA 🐐", "exito")

web_servir(8080)
```
# GRAN DISCLAIMER
Ahora mismo la creacion de OS esta muy bugueada por culpa de la transicion a Rust y otros cambios. Espero poder solucionarlo en la 4.1

## 💻 Bajo Nivel: Creación de Sistemas (OS Mode)

Mesa es capaz de hablarle directamente al procesador. Crea sectores de arranque (Bootsector) de 512 bytes con normalización de segmentos real:

```mesa
-- plantilla_os.mesa
asm = x86_nuevo()
iniciar_boot(asm)
modo_video(asm, 0x13)

apuntar(asm, 0x7C00, "Hola desde MesaOS Nativo")
llamar(asm, "print_str")

-- Compilar a binario real de 512 bytes
codigo = compilar(asm)
boot = bootsector(codigo)
archivo_escribir_bytes("mesa.img", boot)
```

## 🛠️ Características Principales
- 🌐 **Web Stack**: Servidor HTTP Real, Cliente `reqwest` integrado y generador de interfaces dinámicas.
- 🔐 **Seguridad**: Implementación nativa de SHA256, BCrypt, HMAC y gestión de tokens.
- 🗄️ **Persistencia**: Soporte directo para SQLite, CSV y JSON con acceso optimizado.
- ⚡ **Performance**: Motor nativo en Rust con manejo eficiente de memoria y tipos `Range` para slicing veloz.
- 🔧 **Low-Level**: Toolkit x86 integrado con soporte para etiquetas, saltos lejanos y manipulación de VRAM.

---

## 📦 Instalación Rápida (v4.0.0)
Para instalar el núcleo nativo en tu sistema Linux:

```bash
git clone https://github.com/crackanimad0r/Mesa-LP.git
cd Mesa-LP/mesa-core
cargo build --release
cp target/release/mesa-core ../mesa
cd ..
./mesa ayuda
```

---

## 🗺️ Mesa-LP Roadmap

### 🟢 v4.0.0 — **Estado Actual** (Independencia Total) ✅
- [x] **Runtime en Rust**: Eliminación total de la dependencia de Python.
- [x] **Servidor HTTP Real**: Implementación de `TcpListener` para web hosting real.
- [x] **Slicing Nativo**: Soporte para rangos `[1..]` y manipulación de datos a alta velocidad.
- [x] **MesaOS v2**: Estabilidad de bootloader corregida y normalización de segmentos.
- [x] **Bilingüismo Nativo**: Paridad de lexer y parser para ES/EN.

---

### � v4.1.0 — **Próximamente** (Ecosistema Global)
- [ ] **Mesa-Wasm**: Compilación de lógica Mesa directamente a WebAssembly.
- [ ] **Librerías Extendidas**: Integración de drivers de red adicionales para MesaOS.
- [ ] **Self-Hosting**: El compilador Mesa escrito íntegramente en Mesa.

---

## 📖 Documentación
La documentación completa se encuentra en [DOCS.md](./docs/DOCS.md). Incluye detalles de las +200 funciones nativas disponibles.

## 🐐 Autor
Creado por **Crackanimador**. Mesa v4.0.0 es la culminación de un proceso de búsqueda de soberanía tecnológica y potencia bilingüe.


## NOTA IMPORTANTE:
En el desarrollo de este lenguaje, usé IA para la programación, ya que todavía no tengo todos los conocimientos necesarios (estoy todavía en educación obligatoria, por favor).

## 🤝 Contribuir
Si quieres ayudar a que Mesa sea el lenguaje definitivo, ¡los Pull Requests son bienvenidos! 

---

## ------------------------------------------------------ENGLISH----------------------------------------------

# 🐐 Mesa Language v4.0.0 — NATIVE (THE FINAL LEAP)

**Mesa** is a bilingual, sovereign programming language designed to break down the barriers between high-level development and systems engineering. With the release of **v4.0.0**, Mesa has transitioned to a **100% Native Rust engine**, completely eliminating Python dependencies and delivering unprecedented speed and stability.

---

## 🚀 Why Mesa?

* **Total Sovereignty:** +200 built-in native functions. Forget about `npm install` or `pip install`. HTTP (Sync/Async), Cryptography, Databases, and JSON are standard.
* **Bilingual by Design:** Program in Spanish or English without aliases or workarounds. `decir()` is as powerful as `say()`. Total parity in every line.
* **From Web to Hardware:** Write a complete web application with real servers in 20 lines or dive down to the x86 register level to create your own OS with the native toolkit.
* **Native Engine (Rust):** Goodbye to Python-interpreted bytecode. Mesa now runs directly on a high-performance runtime written in Rust.

---

## 🎨 High Level: Web Builder with Real Server
Mesa eliminates web development frustration. No more endless tags or simulations—just pure logic and **native HTTP servers (`TcpListener`)**.

```mesa
-- A professional website in seconds
page(“Mesa World”, “ocean”)

navbar(“Mesa”, [[“Home”, “/”], [“Docs”, “/docs”]])

title(“Welcome to the Future”)
text(“Build powerful websites with real servers without writing a single line of HTML.”)

card(“Sovereignty”, “Mesa doesn't depend on external libraries.”)
alert(“Mesa is THE GOAT 🐐”, “success”)

serve_web(8080)
```
# MAJOR DISCLAIMER
Currently, OS creation is very buggy due to the transition to Rust and other changes. I hope to fix this in version 4.1

## 💻 Low Level: System Creation (OS Mode)

Mesa can communicate directly with the processor. Create 512-byte boot sectors with real segment normalization:

```mesa
-- template_os.mesa
asm = x86_new()
start_boot(asm)
video_mode(asm, 0x13)

point(asm, 0x7C00, “Hello from Native MesaOS”)
call(asm, “print_str”)

-- Compile to real 512-byte binary
code = compile(asm)
boot = bootsector(code)
write_bytes_to_file(“mesa.img”, boot)
```

## 🛠️ Key Features
- 🌐 **Web Stack**: Real HTTP server, integrated `reqwest` client, and dynamic interface generator.
- 🔐 **Security**: Native implementation of SHA256, BCrypt, HMAC, and token management.
- 🗄️ **Persistence**: Direct support for SQLite, CSV, and JSON with optimized access.
- ⚡ **Performance**: Native Rust engine with efficient memory handling and `Range` types for fast slicing.
- 🔧 **Low-Level**: Integrated x86 toolkit with support for labels, far jumps, and VRAM manipulation.

---

## 📦 Quick Installation (v4.0.0)
To install the native core on your Linux system:

```bash
git clone https://github.com/crackanimad0r/Mesa-LP.git
cd Mesa-LP/mesa-core
cargo build --release
cp target/release/mesa-core ../mesa
cd ..
./mesa help
```

---

## �️ Mesa-LP Roadmap

### 🟢 v4.0.0 — **Current State** (Total Independence) ✅
- [x] **Rust Runtime**: Total elimination of Python dependencies.
- [x] **Real HTTP Server**: `TcpListener` implementation for real web hosting.
- [x] **Native Slicing**: Support for `[1..]` ranges and high-speed data manipulation.
- [x] **MesaOS v2**: Fixed bootloader stability and segment normalization.
- [x] **Native Bilinguism**: Lexer and Parser parity for ES/EN.

---

### 🟡 v4.1.0 — **Upcoming** (Global Ecosystem)
- [ ] **Mesa-Wasm**: Compiling Mesa logic directly to WebAssembly.
- [ ] **Extended Libraries**: Additional network driver integration for MesaOS.
- [ ] **Self-Hosting**: Mesa compiler written entirely in Mesa.

---

## 📖 Documentation
The complete documentation can be found in [DOCS.md](./docs/DOCS.md).

## 🐐 Author
Created by **Crackanimador**. Mesa v4.0.0 is the culmination of a journey for technological sovereignty and bilingual power.

## IMPORTANT NOTE:
In developing this language, I used AI for the programming, as I don’t yet have all the necessary knowledge (I’m still in school, please).

## 🤝 Contribute
If you want to help make Mesa the definitive language, pull requests are welcome!

<img width="1920" height="969" alt="Captura desde 2026-04-01 09-37-43" src="https://github.com/user-attachments/assets/9243233a-2802-4bd6-845e-4f707256eacb" />
<img width="776" height="514" alt="Captura desde 2026-03-31 12-31-57" src="https://github.com/user-attachments/assets/3d637eec-a210-4caf-9ca1-052e9323b32d" />
