# Project Cleanup Report

Generated: 2026-03-03

## Summary

| Category | Count | Size |
|----------|-------|------|
| Python cache files | ~19,912 | ~50MB+ |
| .DS_Store files | 3 | ~18KB |
| Test output files | 3 | ~1MB |
| Duplicate/Temp voice files | 2 | ~15MB |
| Virtual environment | 1 | 1.7GB |

---

## Recommended Cleanups

### 1. Python Cache Files (Safe to Delete)
```bash
# Remove all __pycache__ and .pyc files
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null
```
**Impact:** Frees ~50MB, improves git status readability

---

### 2. macOS .DS_Store Files (Safe to Delete)
```bash
# Remove macOS system files
find . -name ".DS_Store" -type f -delete
```
**Files found:**
- `./.DS_Store`
- `./CosyVoice2-Yue/.DS_Store`
- `./CosyVoice2-Yue/asset/.DS_Store`

**Impact:** Frees ~18KB, already in .gitignore

---

### 3. Test Output Files (Optional)
```bash
# Remove test output directories
cd CosyVoice2-Yue
rm -rf output/ output_female/
```
**Files:**
- `output/base_0.wav` (338KB)
- `output/zjg_0.wav` (290KB)
- `output_female/base_0.wav` (338KB)

**Impact:** Frees ~1MB, these are old test outputs

---

### 4. Redundant Voice Files (Review First)

**Potential duplicates in `asset/`:**

| File | Size | Status |
|------|------|--------|
| `hk_female.wav` | 818KB | ✅ Used (default voice) |
| `hk_female_2.wav` | 13MB | ⚠️  Possible duplicate - remove? |
| `luis_neng.wav` | 1.4MB | ⚠️  Personal file - remove? |
| `yue_male.wav` | 3.8MB | ✅ Used |
| `yue_female.wav` | 1.7MB | ✅ Used |
| `hk_male.wav` | 884KB | ✅ Used |

**Recommended action:**
```bash
cd CosyVoice2-Yue/asset
# Remove duplicate/large variant
rm hk_female_2.wav
# Remove personal file (or move outside repo)
rm luis_neng.wav
```
**Impact:** Frees ~14.4MB

---

### 5. Python Version File (Optional)
```bash
rm CosyVoice2-Yue/.python-version
```
**Impact:** Removes pyenv version file (not needed in repo)

---

### 6. Old Test Scripts (Review First)

The following test scripts may be redundant now that we have `openai_server.py`:

| File | Size | Status |
|------|------|--------|
| `test_tts.py` | 8.1KB | ⚠️  Old test - keep for reference? |
| `test_tts2.py` | 1.2KB | ⚠️  Old test - remove? |
| `test_tts_advanced.py` | 3.0KB | ⚠️  Old test - keep for reference? |

**Note:** Keep these if they're useful for direct model testing without the server.

---

### 7. Virtual Environment (DO NOT DELETE, but exclude)

The `.venv` directory is already in `.gitignore` and not tracked by git.

**Size:** 1.7GB
**Action:** Already properly excluded from git

---

## Cleanup Script

Create this as `cleanup.sh` and run it:

```bash
#!/bin/bash
# Safe cleanup script for CosyVoice2-Yue

echo "Cleaning up project..."

# 1. Python cache
echo "Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null

# 2. macOS files
echo "Removing .DS_Store files..."
find . -name ".DS_Store" -type f -delete

# 3. Test outputs (optional - comment out if you want to keep)
echo "Removing test outputs..."
rm -rf CosyVoice2-Yue/output/ CosyVoice2-Yue/output_female/

# 4. Remove pyenv version file (optional)
rm -f CosyVoice2-Yue/.python-version

echo "Cleanup complete!"
```

---

## Files to Review (Manual Decision)

These files need your review before deletion:

1. **`CosyVoice2-Yue/asset/hk_female_2.wav`** (13MB)
   - Appears to be a duplicate of `hk_female.wav`
   - Not referenced in `openai_server.py`

2. **`CosyVoice2-Yue/asset/luis_neng.wav`** (1.4MB)
   - Personal voice file
   - Not referenced in code

3. **Old test scripts:**
   - `test_tts.py`
   - `test_tts2.py`
   - `test_tts_advanced.py`

---

## Post-Cleanup Size Estimate

| Item | Current | After Cleanup |
|------|---------|---------------|
| Total repo | ~13GB | ~13GB (no model change) |
| Git-tracked files | ~45MB | ~25MB |
| Cache/temp files | ~50MB | ~0 |

---

## Recommended .gitignore Updates

The `.gitignore` is already good, but could add:

```gitignore
# Audio outputs
*.wav
*.mp3
!asset/*.wav  # Keep reference audio files

# Temporary files
*.tmp
*.bak
*.log

# IDE
*.sublime-*
```
