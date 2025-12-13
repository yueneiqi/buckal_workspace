use std::{collections::HashMap, process::Command, str::FromStr, sync::OnceLock};

use cargo_platform::Cfg;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct TargetTriple {
    pub arch: Arch,
    pub vendor: Vendor,
    pub os: Os,
    pub env: Env, // ABI
}

impl std::fmt::Display for TargetTriple {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        if self.env == Env::None {
            write!(f, "{}-{}-{}", self.arch, self.vendor, self.os)
        } else {
            write!(f, "{}-{}-{}-{}", self.arch, self.vendor, self.os, self.env)
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum Arch {
    X86_64,
    Aarch64,
    I686,
}

impl std::fmt::Display for Arch {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        f.write_str(match self {
            Arch::X86_64 => "x86_64",
            Arch::Aarch64 => "aarch64",
            Arch::I686 => "i686",
        })
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum Vendor {
    Unknown,
    Apple,
    Pc,
}

impl std::fmt::Display for Vendor {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        f.write_str(match self {
            Vendor::Unknown => "unknown",
            Vendor::Apple => "apple",
            Vendor::Pc => "pc",
        })
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum Os {
    Linux,
    Windows,
    Darwin,
}

impl std::fmt::Display for Os {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        f.write_str(match self {
            Os::Linux => "linux",
            Os::Windows => "windows",
            Os::Darwin => "darwin",
        })
    }
}

impl Os {
    pub fn as_str(&self) -> &'static str {
        match self {
            Os::Linux => "linux",
            Os::Windows => "windows",
            Os::Darwin => "darwin",
        }
    }
}

impl AsRef<str> for Os {
    fn as_ref(&self) -> &str {
        self.as_str()
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum Env {
    Gnu,
    Msvc,
    None,
}

impl std::fmt::Display for Env {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        f.write_str(match self {
            Env::Gnu => "gnu",
            Env::Msvc => "msvc",
            Env::None => "",
        })
    }
}

macro_rules! rustc_target {
    ($arch:ident, $vendor:ident, $os:ident, $env:ident) => {
        TargetTriple {
            arch: Arch::$arch,
            vendor: Vendor::$vendor,
            os: Os::$os,
            env: Env::$env,
        }
    };
}

pub const SUPPORTED_TARGETS: &[TargetTriple] = &[
    // Tier 1 targets supported by Rust
    rustc_target!(Aarch64, Apple, Darwin, None),
    rustc_target!(Aarch64, Pc, Windows, Msvc),
    rustc_target!(Aarch64, Unknown, Linux, Gnu),
    rustc_target!(I686, Pc, Windows, Msvc),
    rustc_target!(I686, Unknown, Linux, Gnu),
    rustc_target!(X86_64, Pc, Windows, Gnu),
    rustc_target!(X86_64, Pc, Windows, Msvc),
    rustc_target!(X86_64, Unknown, Linux, Gnu),
];

static TARGET_CFG_SET: OnceLock<HashMap<String, Vec<Cfg>>> = OnceLock::new();

pub fn get_cfg_set(target_triple: &str) -> Option<&'static [Cfg]> {
    let cache = TARGET_CFG_SET.get_or_init(|| {
        let mut map: HashMap<String, Vec<Cfg>> = HashMap::new();
        for target in SUPPORTED_TARGETS {
            let triple = target.to_string();
            if let Ok(output) = Command::new("rustc")
                .args(["--print=cfg", "--target", &triple])
                .output()
            {
                if output.status.success() {
                    let cfgs: Vec<Cfg> = String::from_utf8_lossy(&output.stdout)
                        .lines()
                        .map(|line| Cfg::from_str(line).unwrap())
                        .collect();
                    map.insert(triple, cfgs);
                }
            }
        }
        map
    });

    cache.get(target_triple).map(|v| v.as_slice())
}