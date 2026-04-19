// Mesa v4.0.0 - Native Scaffolding in Rust
// Logic for creating new Mesa projects from templates

use std::fs;
use std::path::Path;

pub struct Scaffolder;

impl Scaffolder {
    pub fn create_project(template: &str, name: &str) -> Result<(), String> {
        println!("✨ Creando nuevo proyecto '{}' con plantilla '{}'...", name, template);
        
        let root = Path::new(name);
        fs::create_dir_all(root).map_err(|e| e.to_string())?;
        
        match template {
            "basico" | "basic" => {
                fs::write(root.join("main.mesa"), "-- Hola Mundo en Mesa\ndecir(\"¡Hola desde el nuevo proyecto!\")\n").map_err(|e| e.to_string())?;
                fs::write(root.join("mesa_pkg.json"), format!(r#"{{ "name": "{}", "version": "1.0.0" }}"#, name)).map_err(|e| e.to_string())?;
            }
            "libreria" | "lib" => {
                let lib_file = format!("{}.mesa", name);
                fs::write(root.join(&lib_file), format!("-- Librería {}\nfuncion hola() {{ dar \"Hola desde {}!\" }}\n", name, name)).map_err(|e| e.to_string())?;
                fs::create_dir_all(root.join("tests")).map_err(|e| e.to_string())?;
                fs::write(root.join("tests").join("test_main.mesa"), format!("usar \"{}\"\nusar \"test\"\n\nes_igual(hola(), \"Hola desde {}!\", \"hola() funciona\")\n", name, name)).map_err(|e| e.to_string())?;
                fs::write(root.join("mesa_pkg.json"), format!(r#"{{ "name": "{}", "version": "1.0.0", "type": "library" }}"#, name)).map_err(|e| e.to_string())?;
            }
            _ => return Err(format!("Plantilla '{}' desconocida.", template)),
        }
        
        println!("✅ Proyecto '{}' creado satisfactoriamente.", name);
        Ok(())
    }
}
