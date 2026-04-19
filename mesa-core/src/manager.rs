// Mesa v4.0.0 - Native Package Manager in Rust
// Logic for installing, publishing and listing packages

use std::path::PathBuf;
use std::fs;

pub struct PackageManager;

impl PackageManager {
    pub fn get_mesa_home() -> PathBuf {
        let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
        home.join(".mesa")
    }

    pub fn get_pkg_dir() -> PathBuf {
        Self::get_mesa_home().join("packages")
    }

    pub fn install(name: &str, _url: Option<&str>) -> Result<(), String> {
        println!("📦 Instalando paquete '{}'...", name);
        
        let pkg_root = PathBuf::from(name);
        if pkg_root.exists() {
            let dest = Self::get_pkg_dir().join(name);
            fs::create_dir_all(&dest).map_err(|e| e.to_string())?;
            // Copy logic (minimal)
            Self::copy_dir(&pkg_root, &dest)?;
            println!("✅ Paquete '{}' instalado correctamente en ~/.mesa/packages", name);
            return Ok(());
        }
        
        Err(format!("Paquete '{}' no encontrado localmente. (Download not implemented in this version)", name))
    }

    pub fn publish(path: &str, _web: bool) -> Result<(), String> {
        println!("🚀 Publicando paquete desde '{}'...", path);
        // Minimal mimic: just copy to a local "registry" or mesa_pkgs
        let src = PathBuf::from(path);
        let name = src.file_name().unwrap().to_str().unwrap();
        let dest = PathBuf::from("mesa_pkgs").join(name);
        
        fs::create_dir_all(&dest).map_err(|e| e.to_string())?;
        Self::copy_dir(&src, &dest)?;
        
        println!("✅ Paquete '{}' publicado correctamente en mesa_pkgs/", name);
        Ok(())
    }

    fn copy_dir(src: &std::path::Path, dst: &std::path::Path) -> Result<(), String> {
        for entry in fs::read_dir(src).map_err(|e| e.to_string())? {
            let entry = entry.map_err(|e| e.to_string())?;
            let path = entry.path();
            if path.is_file() {
                let name = path.file_name().unwrap();
                let dest_file = dst.join(name);
                fs::copy(&path, &dest_file).map_err(|e| e.to_string())?;
            } else if path.is_dir() {
                let name = path.file_name().unwrap();
                let dest_dir = dst.join(name);
                fs::create_dir_all(&dest_dir).map_err(|e| e.to_string())?;
                Self::copy_dir(&path, &dest_dir)?;
            }
        }
        Ok(())
    }
}
