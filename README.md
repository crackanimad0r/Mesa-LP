# 🐐 Mesa Language v2.2.0 — LA CABRA

**Mesa** es un lenguaje de programación bilingüe y soberano diseñado para romper las barreras entre el desarrollo de alto nivel y la ingeniería de sistemas. Con una sintaxis humana y un motor de Bytecode optimizado, Mesa te permite construir desde servidores web modernos hasta núcleos de sistemas operativos (Kernels) de 512 bytes.

---

## 🚀 ¿Por qué Mesa?

* **Soberanía Total:** +200 funciones nativas. Olvídate de `npm install` o `pip install`. HTTP, Criptografía, Bases de Datos y JSON vienen integrados.
* **Bilingüe por Diseño:** Programa en Español o Inglés sin alias ni parches. `decir()` es tan potente como `say()`.
* **De la Web al Hierro:** Escribe una aplicación web completa en 20 líneas o baja al nivel de los registros x86 para crear tu propio OS.
* **Compilador x86 Nativo:** Incluye `x86.py`, un compilador que transforma tu código Mesa en binarios reales para hardware real.

---

## 🎨 Alto Nivel: Web sin HTML
Mesa elimina la frustración del desarrollo web. No más etiquetas infinitas, solo lógica pura (aunque puedes usar HTML para personalización avanzada).

```python
-- Una web profesional en segundos
pagina("Mesa World", "oceano")

navbar("Mesa", [["Inicio", "/"], ["Docs", "/docs"]])

titulo("Bienvenido al Futuro")
texto("Crea webs potentes sin escribir ni una línea de HTML.")

tarjeta("Soberanía", "Mesa no depende de librerías externas.")

alerta("Mesa es LA CABRA 🐐", "exito")

web_servir(8080)
```
## 💻 Bajo Nivel: Creación de Sistemas (OS Mode)

Mesa es capaz de hablarle directamente al procesador. Aquí tienes un sector de arranque (Bootsector) funcional escrito en Mesa:

```
-- plantilla_os.mesa
asm = x86_nuevo()
iniciar_boot(asm)
modo_video(asm, 0x03)
limpiar_pantalla(asm)

apuntar(asm, 0x7C00, "Hola desde MesaOS")
llamar(asm, "print_str")

-- Compilar a binario real de 512 bytes
codigo = compilar(asm)
boot = bootsector(codigo)
archivo_escribir_bytes("mesa.img", boot)
```

## 🛠️ Características Principales
- 🌐 Web Stack: Servidor HTTP, Cliente y generador de interfaces integrado.

- 🔐 Seguridad: Implementación nativa de SHA256, HMAC y gestión de contraseñas.

- 🗄️ Persistencia: Soporte directo para SQLite y archivos CSV/JSON.

- ⚡ Concurrencia: Sistema de tareas y canales para procesamiento en paralelo.

- 🔧 Low-Level: Acceso a registros x86, gestión de memoria manual (reservar/liberar) y punteros.

- 📦 Instalación Rápida
Para instalar Mesa en tu sistema Linux (basado en Debian/Ubuntu):

```
git clone [https://github.com/crackanimad0r/Mesa-LP.git](https://github.com/crackanimad0r/Mesa-LP.git)
cd Mesa-LP
chmod +x mesa
source ~/.bashrc
./mesa ayuda/help
```
## 📖 Documentación
La documentación completa de +2000 líneas se encuentra en el archivo DOCS.md. Incluye ejemplos detallados de cada una de las 200+ funciones nativas.

## 🐐 Autor
Creado por Crackanimador en una ilustración de conocimientos por aburrimiento de desarrollo de 48 horas (Finalizado el 31 de Marzo).

## NOTA IMPORTANTE:
 En el desarrollo de este lenguaje, usé IA para la programación, ya que todavía no tengo todos los conocimientos necesarios (estoy todavía en educación obligatoria, por favor).

## 🤝 Contribuir
Si quieres ayudar a que Mesa sea el lenguaje definitivo, ¡los Pull Requests son bienvenidos! Revisa nuestra sección de tareas pendientes.

Próximamente: Sistema de librerías de código externas. Lanzaré documentación sobre cómo hacerlo cuando esté programado.

Mesa Language - Codifica con Poder. Codifica en tu Idioma.

## ------------------------------------------------------ENGLISH----------------------------------------------

**Mesa** is a bilingual, sovereign programming language designed to break down the barriers between high-level development and systems engineering. With a human-friendly syntax and an optimized bytecode engine, Mesa lets you build everything from modern web servers to 512-byte operating system kernels.

---

## 🚀 Why Mesa?

* **Total Sovereignty:** +200 native functions. Forget about `npm install` or `pip install`. HTTP, Cryptography, Databases, and JSON are built-in.
* **Bilingual by Design:** Program in Spanish or English without aliases or workarounds. `decir()` is just as powerful as `say()`.
* **From Web to Hardware:** Write a complete web application in 20 lines or dive down to the x86 register level to create your own OS.
* **Native x86 Compiler:** Includes `x86.py`, a compiler that transforms your Mesa code into real binaries for real hardware.

---

## 🎨 High Level: Web Without HTML
Mesa eliminates the frustration of web development. No more endless tags, just pure logic (though you can use HTML for advanced customization).

```python
-- A professional website in seconds
page(“Mesa World”, “ocean”)

navbar(“Mesa”, [[“Home”, “/”], [‘Docs’, “/docs”]])

title(“Welcome to the Future”)
text(“Build powerful websites without writing a single line of HTML.”)

card(“Sovereignty”, “Mesa doesn't depend on external libraries.”)

alert(“Mesa is THE GOAT 🐐”, “success”)

serve_web(8080)
```
## 💻 Low Level: System Creation (OS Mode)

Mesa can communicate directly with the processor. Here is a functional boot sector written in Mesa:

```
-- template_os.mesa
asm = x86_new()
start_boot(asm)
video_mode(asm, 0x03)
clear_screen(asm)

point(asm, 0x7C00, “Hello from MesaOS”)
call(asm, “print_str”)

-- Compile to a 512-byte binary
code = compile(asm)
boot = bootsector(code)
write_bytes_to_file(“mesa.img”, boot)
```

## 🛠️ Key Features
- 🌐 Web Stack: HTTP server, client, and integrated interface generator.

- 🔐 Security: Native implementation of SHA256, HMAC, and password management.

- 🗄️ Persistence: Direct support for SQLite and CSV/JSON files.

- ⚡ Concurrency: Task and channel system for parallel processing.

- 🔧 Low-Level: Access to x86 registers, manual memory management (allocate/deallocate), and pointers.

- 📦 Quick Installation
To install Mesa on your Linux system (Debian/Ubuntu-based):

```
git clone [https://github.com/crackanimad0r/Mesa-LP.git](https://github.com/crackanimad0r/Mesa-LP.git)
cd Mesa-LP
chmod +x mesa
source ~/.bashrc
./mesa help/ayuda
```
## 📖 Documentation
The complete documentation, over 2,000 lines long, is located in the DOCS.md file. It includes detailed examples of each of the 200+ native functions.

## 🐐 Author
Created by Crackanimador as a knowledge exercise during a 48-hour development marathon out of boredom (Completed on March 31).

## IMPORTANT NOTE:
 In developing this language, I used AI for the programming, as I don’t yet have all the necessary knowledge (I’m still in school, please).

## 🤝 Contribute
If you want to help make Mesa the definitive language, pull requests are welcome! Check out our to-do list.

Coming soon: External code library system. I’ll release documentation on how to do this when it’s ready.

Mesa Language - Code with Power. Code in Your Own Language.
