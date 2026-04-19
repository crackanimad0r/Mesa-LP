// Mesa CLI v4.0.0 - Native Entry Point
use std::env;
use std::fs;
use std::process::Command;
use std::path::PathBuf;

use mesa_core::lexer::Lexer;
use mesa_core::parser::Parser;
use mesa_core::interpreter::Interpreter;
use mesa_core::manager::PackageManager;
use mesa_core::scaffold::Scaffolder;
use mesa_core::codegen_c::CodegenC;

fn print_help() {
    println!(r#"
 🏓 Mesa Language v4.0.0 — Independencia Total
 
 USO: mesa [comando] <archivo>
 
 COMANDOS:
   correr, run <archivo>     Ejecutar programa nativamente
   compilar, build <arch>    Compilar a binario nativo (vía C)
   instalar <paquete>        Instalar paquete local/remoto
   publicar <paquete>        Publicar paquete en mesa_pkgs
   nuevo <tipo> <nombre>     Crear nuevo proyecto
   ayuda, help               Mostrar ayuda
   version                   Mostrar version
"#);
}

fn run_file(path: &str) {
    let source = match fs::read_to_string(path) {
        Ok(s) => s,
        Err(_) => {
            println!("Archivo no encontrado: {}", path);
            std::process::exit(1);
        }
    };

    let mut lexer = Lexer::new(&source);
    let tokens = lexer.tokenize();
    let mut parser = Parser::new(tokens);
    
    match parser.parse_program() {
        Ok(stmts) => {
            let mut interpreter = Interpreter::new();
            if let Err(e) = interpreter.run(&stmts) {
                eprintln!("\n❌ Error: {}", e.message);
                std::process::exit(1);
            }
        }
        Err(e) => {
            eprintln!("\n❌ Error de Parser: {}", e.message);
            std::process::exit(1);
        }
    }
}

fn compile_file(path: &str) {
    let source = match fs::read_to_string(path) {
        Ok(s) => s,
        Err(_) => {
            println!("Archivo no encontrado: {}", path);
            std::process::exit(1);
        }
    };

    let mut lexer = Lexer::new(&source);
    let tokens = lexer.tokenize();
    let mut parser = Parser::new(tokens);
    
    match parser.parse_program() {
        Ok(stmts) => {
            println!("⚙️ Compilando '{}' nativamente (Backend C)...", path);
            let mut cg = CodegenC::new();
            let c_code = cg.compile(&stmts);
            
            let stem = std::path::Path::new(path).file_stem().unwrap().to_str().unwrap();
            let c_file = format!("{}.c", stem);
            fs::write(&c_file, c_code).unwrap();
            
            println!("🔗 Enlazando con Clang/GCC...");
            let status = Command::new("clang")
                .arg(&c_file)
                .arg("-o")
                .arg(stem)
                .arg("-lm")
                .status();
            
            if status.is_ok() && status.unwrap().success() {
                println!("✨ ¡Éxito! Binario generado: ./{}", stem);
                let _ = fs::remove_file(c_file);
            } else {
                println!("❌ Error en el enlazado.");
            }
        }
        Err(e) => {
            eprintln!("\n❌ Error de Parser: {}", e.message);
            std::process::exit(1);
        }
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        print_help();
        return;
    }

    let cmd = args[1].to_lowercase();
    match cmd.as_str() {
        "ayuda" | "help" | "--help" | "-h" => print_help(),
        "version" | "-v" => println!("Mesa Language v4.0.0 (Native Rust Core)"),
        "correr" | "run" => {
            if args.len() < 3 { println!("Uso: mesa correr <archivo>"); }
            else { run_file(&args[2]); }
        }
        "compilar" | "build" => {
            if args.len() < 3 { println!("Uso: mesa compilar <archivo>"); }
            else { compile_file(&args[2]); }
        }
        "instalar" | "install" => {
            if args.len() < 3 { println!("Uso: mesa instalar <paquete>"); }
            else { 
                if let Err(e) = PackageManager::install(&args[2], None) { println!("❌ Error: {}", e); }
            }
        }
        "publicar" | "publish" => {
            if args.len() < 3 { println!("Uso: mesa publicar <paquete>"); }
            else { 
                if let Err(e) = PackageManager::publish(&args[2], false) { println!("❌ Error: {}", e); }
            }
        }
        "nuevo" | "new" => {
            if args.len() < 4 { println!("Uso: mesa nuevo <tipo> <nombre>"); }
            else { 
                if let Err(e) = Scaffolder::create_project(&args[2], &args[3]) { println!("❌ Error: {}", e); }
            }
        }
        path => {
            if std::path::Path::new(path).exists() {
                run_file(path);
            } else if std::path::Path::new(&format!("{}.mesa", path)).exists() {
                run_file(&format!("{}.mesa", path));
            } else {
                println!("Comando o archivo desconocido: {}", path);
                println!("Usa 'mesa ayuda' para ver los comandos");
            }
        }
    }
}
