//! Sample files for a card, with size limits and path safety.

use std::path::{Component, Path, PathBuf};
use std::{fs, io};

pub const MAX_FILES: usize = 2000;
pub const MAX_BYTES: usize = 512 * 1024;

fn invalid(message: &str) -> io::Error {
    io::Error::new(io::ErrorKind::InvalidInput, message.to_string())
}

// list returns every regular file under root with its size, sorted by path.
pub fn list(root: &Path) -> io::Result<Vec<(String, u64)>> {
    let mut found = Vec::new();
    let mut pending = vec![root.to_path_buf()];
    while let Some(dir) = pending.pop() {
        for entry in fs::read_dir(&dir)? {
            let entry = entry?;
            let kind = entry.file_type()?;
            if kind.is_dir() {
                pending.push(entry.path());
            } else if kind.is_file() && found.len() < MAX_FILES {
                let relative = entry
                    .path()
                    .strip_prefix(root)
                    .map_err(io::Error::other)?
                    .to_owned();
                found.push((
                    relative.to_string_lossy().into_owned(),
                    entry.metadata()?.len(),
                ));
            }
        }
    }
    found.sort();
    Ok(found)
}

// within resolves relative under root, refusing anything that would leave it.
pub fn within(root: &Path, relative: &str) -> io::Result<PathBuf> {
    let relative = Path::new(relative);
    if !relative
        .components()
        .all(|part| matches!(part, Component::Normal(_)))
    {
        return Err(invalid("path must stay inside the sample"));
    }
    let path = root.join(relative);
    if !path.canonicalize()?.starts_with(root.canonicalize()?) {
        return Err(invalid("path must stay inside the sample"));
    }
    Ok(path)
}

// read returns the contents of a file under root, refusing anything that would leave it.
pub fn read(root: &Path, relative: &str) -> io::Result<(String, bool)> {
    let path = within(root, relative)?;
    if !fs::symlink_metadata(&path)?.is_file() {
        return Err(invalid("not a regular file"));
    }
    let bytes = fs::read(&path)?;
    let truncated = bytes.len() > MAX_BYTES;
    let shown = &bytes[..bytes.len().min(MAX_BYTES)];
    Ok((String::from_utf8_lossy(shown).into_owned(), truncated))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample() -> PathBuf {
        static SEQ: std::sync::atomic::AtomicUsize = std::sync::atomic::AtomicUsize::new(0);
        let n = SEQ.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
        let dir = std::env::temp_dir().join(format!("idr-sample-{}-{n}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        fs::create_dir_all(dir.join("lib")).unwrap();
        fs::write(dir.join("package.json"), "{}").unwrap();
        fs::write(dir.join("lib/index.js"), "fetch(url);\n").unwrap();
        dir
    }

    #[test]
    fn lists_nested_files_relative_to_the_sample() {
        let root = sample();
        let names: Vec<String> = list(&root)
            .unwrap()
            .into_iter()
            .map(|(name, _)| name)
            .collect();
        assert_eq!(names, vec!["lib/index.js", "package.json"]);
    }

    #[test]
    fn refuses_paths_that_leave_the_sample() {
        let root = sample();
        for bad in ["../x", "/etc/passwd", "lib/../../x", ""] {
            assert!(read(&root, bad).is_err(), "should refuse {bad:?}");
        }
        assert_eq!(read(&root, "lib/index.js").unwrap().0, "fetch(url);\n");
    }

    #[cfg(unix)]
    #[test]
    fn never_follows_a_symlink_out_of_the_sample() {
        let root = sample();
        std::os::unix::fs::symlink("/etc", root.join("escape")).unwrap();
        std::os::unix::fs::symlink("/etc/hostname", root.join("host")).unwrap();
        assert!(read(&root, "escape/hostname").is_err());
        assert!(read(&root, "host").is_err());
        assert!(list(&root)
            .unwrap()
            .iter()
            .all(|(name, _)| !name.starts_with("escape")));
    }

    #[test]
    fn cuts_a_large_file_and_says_so() {
        let root = sample();
        fs::write(root.join("big.js"), vec![b'a'; MAX_BYTES + 10]).unwrap();
        let (text, truncated) = read(&root, "big.js").unwrap();
        assert!(truncated);
        assert_eq!(text.len(), MAX_BYTES);
    }
}
