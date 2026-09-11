//! Baca pair + tulis keputusan audit, file-backed.
//!
//! Dataset input (`pairs.jsonl`, `kb.jsonl`) hanya pernah dibaca. Keputusan
//! ditulis ke file terpisah, dan runner Python membaca file yang sama — jadi
//! formatnya sengaja tetap JSON/JSONL biasa, bukan database.

use serde_json::{Map, Value};
use std::path::{Path, PathBuf};
use std::{fs, io};

pub struct Store {
    pub data_dir: PathBuf,
}

/// Nama file yang dipakai, plus fallback sample supaya UI tetap hidup sebelum
/// dataset asli ada (M1-2).
fn resolve(dir: &Path, name: &str, sample: &str) -> PathBuf {
    let real = dir.join(name);
    if real.exists() {
        real
    } else {
        dir.join(sample)
    }
}

pub fn read_jsonl(path: &Path) -> io::Result<Vec<Value>> {
    if !path.exists() {
        return Ok(Vec::new());
    }
    let text = fs::read_to_string(path)?;
    text.lines()
        .filter(|l| !l.trim().is_empty())
        .map(|l| serde_json::from_str(l).map_err(io::Error::other))
        .collect()
}

impl Store {
    pub fn new(data_dir: PathBuf) -> Self {
        Self { data_dir }
    }

    pub fn pairs_path(&self) -> PathBuf {
        resolve(&self.data_dir, "pairs.jsonl", "pairs.sample.jsonl")
    }

    pub fn decisions_path(&self) -> PathBuf {
        self.data_dir.join("audit_decisions.json")
    }

    pub fn pairs(&self) -> io::Result<(String, Vec<Value>)> {
        let path = self.pairs_path();
        let source = path
            .file_name()
            .map(|n| n.to_string_lossy().into_owned())
            .unwrap_or_default();
        Ok((source, read_jsonl(&path)?))
    }

    pub fn decisions(&self) -> io::Result<Map<String, Value>> {
        let path = self.decisions_path();
        if !path.exists() {
            return Ok(Map::new());
        }
        let text = fs::read_to_string(&path)?;
        match serde_json::from_str(&text) {
            Ok(Value::Object(map)) => Ok(map),
            _ => Ok(Map::new()),
        }
    }

    /// Gabungkan patch ke keputusan satu pair, lalu tulis ulang seluruh file.
    ///
    /// Pemanggil WAJIB memegang lock: ini read-modify-write, dan dua request
    /// bersamaan tanpa lock akan saling menimpa keputusan.
    pub fn merge_decision(&self, id: &str, patch: &Value, now: String) -> io::Result<Value> {
        let mut all = self.decisions()?;
        let mut entry = match all.get(id) {
            Some(Value::Object(existing)) => existing.clone(),
            _ => Map::new(),
        };
        if let Value::Object(fields) = patch {
            for (k, v) in fields {
                entry.insert(k.clone(), v.clone());
            }
        }
        entry.insert("at".into(), Value::String(now));

        let merged = Value::Object(entry);
        all.insert(id.to_string(), merged.clone());

        fs::create_dir_all(&self.data_dir)?;
        // Tulis ke file sementara lalu rename: kalau proses mati saat menulis,
        // file keputusan lama tetap utuh alih-alih jadi JSON terpotong.
        let tmp = self.decisions_path().with_extension("json.tmp");
        fs::write(&tmp, serde_json::to_string_pretty(&Value::Object(all))?)?;
        fs::rename(&tmp, self.decisions_path())?;
        Ok(merged)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    // Cargo menjalankan test paralel dalam satu proses, jadi PID saja tidak
    // cukup: tiap test butuh direktorinya sendiri.
    static SEQ: std::sync::atomic::AtomicUsize = std::sync::atomic::AtomicUsize::new(0);

    fn temp_store() -> Store {
        let n = SEQ.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
        let dir = std::env::temp_dir().join(format!("idr-test-{}-{n}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        fs::create_dir_all(&dir).unwrap();
        Store::new(dir)
    }

    #[test]
    fn membaca_jsonl_melewati_baris_kosong() {
        let s = temp_store();
        let p = s.data_dir.join("pairs.jsonl");
        fs::write(&p, "{\"id\":\"a\"}\n\n{\"id\":\"b\"}\n").unwrap();
        let rows = read_jsonl(&p).unwrap();
        assert_eq!(rows.len(), 2);
    }

    #[test]
    fn file_belum_ada_bukan_error() {
        let s = temp_store();
        assert!(s.decisions().unwrap().is_empty());
        assert!(read_jsonl(&s.data_dir.join("hilang.jsonl")).unwrap().is_empty());
    }

    #[test]
    fn jatuh_ke_sample_saat_dataset_asli_belum_ada() {
        let s = temp_store();
        fs::write(s.data_dir.join("pairs.sample.jsonl"), "{\"id\":\"a\"}\n").unwrap();
        assert!(s.pairs_path().ends_with("pairs.sample.jsonl"));
        fs::write(s.data_dir.join("pairs.jsonl"), "{\"id\":\"b\"}\n").unwrap();
        assert!(s.pairs_path().ends_with("pairs.jsonl"));
    }

    #[test]
    fn patch_menggabung_bukan_menimpa() {
        let s = temp_store();
        s.merge_decision("p1", &json!({"label": "benign"}), "t1".into()).unwrap();
        let out = s
            .merge_decision("p1", &json!({"note": "ragu"}), "t2".into())
            .unwrap();
        // label lama harus bertahan setelah patch kedua
        assert_eq!(out["label"], "benign");
        assert_eq!(out["note"], "ragu");
        assert_eq!(out["at"], "t2");
    }

    #[test]
    fn keputusan_pair_lain_tidak_ikut_hilang() {
        let s = temp_store();
        s.merge_decision("p1", &json!({"label": "benign"}), "t1".into()).unwrap();
        s.merge_decision("p2", &json!({"label": "malicious"}), "t2".into()).unwrap();
        let all = s.decisions().unwrap();
        assert_eq!(all.len(), 2);
        assert_eq!(all["p1"]["label"], "benign");
    }
}
