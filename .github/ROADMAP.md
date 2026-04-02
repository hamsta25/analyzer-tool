# analyzer-tool: Roadmap & Product Plan

## Situazione Attuale

Dal log condiviso:
- ffmpeg rilevato correttamente
- Tesseract rilevato correttamente
- **Problema bloccante**: `setup.ps1` risolve `python` da MSYS2 (`C:/msys64/ucrt64/bin/python.exe`), che non ha pip
- Conseguenza: install dipendenze fallisce ma script continua con messaggio fuorviante "Python deps installed."

**Root cause**: MSYS2 aggiunge `C:\msys64\ucrt64\bin` al PATH prima di Python.org; PowerShell lo trova per primo; MSYS2 python manca di pip perché dipendenza opzionale su quella piattaforma.

---

## Decisioni Prodotto Approvate

1. **Priorità immediata**: Fase A (setup fix) + Fase B (README PATH)
2. **Obiettivo trimestrale AI**: RAG locale su documenti personali (no training da zero)
3. **Connettività**: Offline-first con web search opzionale on-demand
4. **Sicurezza**: Cifratura AES + passphrase su knowledge base
5. **Scope escluso nel breve periodo**: Training from scratch di foundation model comparabile a o1/Sonnet

---

## Program Increment Professionale (Q2 2026)

### Priorita Vincolante

1. **P0**: CI/CD + Security baseline
2. **P1**: OCR quality uplift per handwritten technical notes
3. **P2**: Packaging, release, publication readiness
4. **P3**: Web URL Input — video e PDF da link HTTP/HTTPS, Google Drive, piattaforme web

### Milestone e Stato

| Milestone | Stato | Obiettivo | Verifica minima |
|---|---|---|---|
| M0 Governance | In Progress | Source of truth e agent workflow | ROADMAP aggiornato + PM agent attivo |
| M1 CI/CD | Planned | Pipeline multi-OS con smoke checks | workflow CI verde su PR |
| M2 Security | Planned | Audit dipendenze + SBOM + policy | workflow security verde |
| M3 OCR Quality A | Planned | Profili OCR fast/balanced/max-quality | benchmark OCR su dataset tecnico |
| M4 OCR Quality B | Planned | Layout-aware extraction region-based | miglior retention strutturale |
| M5 Release Engineering | Planned | Versioning/changelog/release checklist | go/no-go report completo |
| M6 Web URL Input | In Progress | Accetta URL HTTP/HTTPS come input per video/PDF | `analyzer.py video <gdrive-url>` trascrisce correttamente |

### Definition of Done (DoD)

- **P0 DoD**:
  - CI e Security workflow in `.github/workflows/` attivi su PR e push.
  - `setup.ps1` e script diagnostici impediscono false positive su ambiente Python.
  - Nessun blocker high/critical aperto in dependency audit.
- **P1 DoD**:
  - OCR benchmark su note handwritten tecniche con confronto baseline.
  - Output markdown mantiene riferimenti visuali/pagina dove necessario.
  - Fallimenti noti documentati con fallback chiaro.
- **P2 DoD**:
  - Checklist release completa (qualita, sicurezza, reproducibility).
  - Documentazione di install/deploy multi-target aggiornata.
- **P3 DoD**:
  - `analyzer.py video <url>` e `analyzer.py pdf <url>` funzionano con URL HTTP/HTTPS.
  - Google Drive shared video link scaricato e trascritto correttamente.
  - Test unitari per `url_resolver.py` (mocked) e test di integrazione con URL reale.
  - `yt-dlp` aggiunto a `requirements.txt`; cleanup automatico del file temporaneo.

### KPI Operativi

- CI success rate su PR >= 95%
- Tempo medio triage vulnerabilita <= 3 giorni lavorativi
- OCR regression rate su dataset benchmark <= baseline attuale
- Incidenti ambiente python/pip/py in setup: trend a zero

### Risk Register (Top 5)

| ID | Rischio | Impatto | Mitigazione |
|---|---|---|---|
| R1 | Mismatch python/pip/py su Windows | Alto | env-doctor + remediation script + CI checks |
| R2 | Vulnerabilita dipendenze non viste | Alto | security workflow con pip-audit |
| R3 | Regressioni OCR su note tecniche | Alto | benchmark + OCR audit skill |
| R4 | Scope creep senza evidenza | Medio | PM agent + DoD gate |
| R5 | Release non riproducibili | Medio | SBOM + checklist release |

### Next OCR Implementation Steps (Engineering Detail)

#### OCR Step A: Quality Profiles (fast, balanced, max-quality)

**Target file**: `src/pdf_analyzer.py`

**Changes**:
1. Introduce `--ocr-profile` with presets:
  - `fast`: lower DPI, conservative timeout, minimal preprocessing
  - `balanced`: current defaults
  - `max-quality`: higher DPI, stronger cleanup, longer timeout
2. Auto-map profile to Tesseract/OCRmyPDF settings (`psm`, language merge, preprocessing flags)
3. Emit profile metadata in markdown header for reproducibility

**Acceptance checks**:
- CLI exposes profile choices and validates input
- Conversion completes on benchmark set without runtime regressions beyond defined threshold
- Output includes profile traceability metadata

#### OCR Step B: Layout-Aware Region Extraction

**Target file**: `src/pdf_analyzer.py`

**Changes**:
1. Add page region segmentation flow (text blocks + drawings/images)
2. Preserve reading order with deterministic region sorting
3. Emit region references in markdown (page, region id, confidence note)
4. Keep fallback to full-page OCR when segmentation quality is poor

**Acceptance checks**:
- Technical notes with diagrams keep context links in output
- Ordering quality improves versus baseline on representative handwritten pages
- Failure modes are surfaced as explicit warnings, not silent degradation

---

## Plan Esecutivo

### Fase A: Hardening Setup (Immediate)

#### A1. Correggere `setup.ps1`

**Cambiamenti**:
1. Risoluzione interprete robusta: priorità `py -3` > `py` > `python3` > `python`
2. Stampa percorso assoluto interprete risolto e versione per diagnostica
3. **Validazione pip esplicita** prima di tentare install: `python -m pip --version`
4. Se pip assente: messaggio bloccante con diagnostica (`where python`, `py -0p`)
5. Non stampare "Python deps installed" se install fallisce (fail-fast)
6. Comando finale usa interprete risolto (non bare `python`)

**Output atteso**:
```
[1/4] Checking Python...
  Found: Python 3.14.3 at C:\Users\Maria\AppData\Local\Programs\Python\Python314\python.exe

[Validation] Checking pip in C:\Users\...\python.exe...
  Found: pip 24.x from C:\Users\... (python 3.14)

[2/4] Installing Python dependencies...
  (proceeds with correct pip)
```

#### A2. Correggere `setup.sh`

**Cambiamenti**:
1. Stessa logica di fallback interprete: preferire `python3`, fallback `python`
2. Validazione pip prima di install (coerente con PS1)
3. **Bonus security**: controllare che interprete NON sia MSYS2 (test `sys.prefix` per escludere msys/mingw)
4. Fail-fast se pip assente
5. Messaggio finale coerente (usa `$PY` in tutti i comandi, non bare `python`)

#### A3. Uniformare messaggistica finale

Entrambi gli script al termine suggeriscono:
```
Try: python src/analyzer.py --help
```

Deve essere:
```
Try: <resolved-interpreter> src/analyzer.py --help
```

Example:
- Windows PowerShell: `Try: C:\Users\Maria\...\python.exe src/analyzer.py --help` oppure `Try: python src/analyzer.py --help` (se path corretto)
- Linux/macOS: `Try: python3 src/analyzer.py --help` (se python3 selezionato)

---

### Fase B: README e Troubleshooting PATH (Immediate)

#### B1. Nuova sezione "Verifying and configuring PATH"

**Posizionamento**: Subito dopo tabella "Tesseract OCR (required...)" e prima di `### Automated setup`

**Contenuto**:
```markdown
### Verifying and configuring PATH

After installing **ffmpeg** or **Tesseract**, ensure they're in your system PATH so the tools can find them.

#### Verify installation

```bash
# Verify ffmpeg
ffmpeg -version

# Verify Tesseract
tesseract --version
```

If either command returns "not found," add them to PATH:

#### Windows (PowerShell / Command Prompt)

**ffmpeg** — common installation paths:
- `C:\Program Files\ffmpeg\bin` (if installed via installer)
- `C:\tools\ffmpeg\bin` (if used Chocolatey without admin)

To add to PATH persistently:
1. Press `Win+X` → Select "System"
2. Click "Advanced system settings" → "Environment Variables"
3. Under "User variables" or "System variables," select `Path` → **Edit**
4. Click **New** and paste the ffmpeg install path
5. Click **OK** and restart your terminal
6. Verify: `ffmpeg -version`

**Tesseract** — typical path: `C:\Program Files\Tesseract-OCR`

Add temporarily (current PowerShell session):
```powershell
$env:PATH += ";C:\Program Files\Tesseract-OCR"
tesseract --version
```

Add persistently (as Administrator in PowerShell):
```powershell
[Environment]::SetEnvironmentVariable("PATH", $env:PATH + ";C:\Program Files\Tesseract-OCR", "User")
# Restart PowerShell to apply
```

#### macOS / Linux

If `brew install` or `apt install` was used, both tools should already be in PATH. Verify:
```bash
which ffmpeg && which tesseract
```

If not found despite installation:
```bash
# Find installation path
find /usr/local/bin -name ffmpeg -o -name tesseract

# Add to shell profile (~/.zshrc, ~/.bashrc, or ~/.bash_profile)
export PATH="/usr/local/bin:$PATH"
source ~/.zshrc  # reload
```

---

#### B2. Troubleshooting section per Python PATH

**New subsection** in README after setup scripts, titled `## Troubleshooting`

**Content template**:
```markdown
### "Python not found" or "pip not found"

Windows users with MSYS2, Git Bash, or Cygwin installed may encounter conflicts:

```powershell
# Check which Python is resolved first
where python
py -0p  # Shows all Python installations and active one
```

If you see `C:\msys64\ucrt64\bin\python.exe` and pip fails:
- **Preferred solution**: Use Windows Python launcher with explicit version:
  ```powershell
  py -3 -m pip install -r requirements.txt
  ```
- Or install Python.org Python (https://www.python.org/downloads/) and ensure it comes first in PATH

If still stuck:
- Run `.\setup.ps1` which now validates pip availability and prints diagnostics
- Review the error message for suggested fixes
```

---

### Fase C: Verifica Post-Fix (Immediate)

#### C1. Test Windows PowerShell

```powershell
# Diagnostica
where python
py -0p
py -3 -m pip --version

# Setup
cd C:\Users\Maria\source\analyzer-tool
.\setup.ps1

# Verifica install
python -m pip show PyMuPDF openai-whisper pytesseract duckduckgo-search pillow

# Smoke test
python src/analyzer.py --help
python src/analyzer.py search "test query" --n 1
```

**Expected**: No "No module named pip" errors; all packages installed; CLI works.

#### C2. Test Linux/macOS bash

```bash
# Diagnostica
which -a python3 python
python3 -m pip --version

# Setup
cd ~/analyzer-tool
bash setup.sh

# Smoke test
python3 src/analyzer.py --help
python3 src/analyzer.py search "test query" --n 1
```

**Expected**: Coerente output; install avvenuto; CLI works.

#### C3. Test ffmpeg/tesseract detection

```bash
# In PowerShell after ffmpeg/Tesseract PATH fix
.\setup.ps1 | Select-String -Pattern "ffmpeg|tesseract"

# Expected: both found
```

---

### Fase D: Espansione Prodotto (Post-Fix, Weeks 2-12)

#### D1. MVP RAG Locale (8-12 settimane)

**Architecture**:
```
Ingestion (analyzer.py reuses pdf/video/web modules)
    ↓
Normalization (normalize.py)
    ↓
Chunking (chunker.py) + YAML metadata
    ↓
Embedding/Indexing (indexer.py) → FAISS + SQLite
    ↓
Retrieval (retriever.py) → semantic BM25 fallback
    ↓
LLM Inference (rag_chat.py) → local Ollama/llama.cpp
    ↓
Encryption (security.py) → AES-256-GCM per knowledge base
    ↓
Distribution (export for edge/microcontroller as Phase 6)
```

#### D2. Nuovi moduli (src/)

| Module | Purpose | Dependencies |
|--------|---------|--------------|
| `config.py` | TOML config + paths + model selection | toml |
| `normalize.py` | Testo → UTF8 + fix encoding + metadata riconoscimento | chardet |
| `chunker.py` | Normalizzato → semantic chunks (512 tokens default) + sliding window | tiktoken |
| `indexer.py` | Chunks → embeddings (distiluse-base multilingual) → FAISS index | sentence-transformers, faiss-cpu, numpy |
| `retriever.py` | Query → top-K semantic results + BM25 fallback | rank-bm25, numpy |
| `rag_chat.py` | Retrieve + LLM inference → answers | ollama Python SDK (light) |
| `security.py` | AES-256-GCM encrypt/decrypt + passphrase derivation (PBKDF2) | cryptography |
| `sync.py` | (Phase 5) Git-like versioning + optional Syncthing export | gitpython (optional) |

#### D3. Flusso Offline-First

```
Default: All operations work offline
  - If `--allow-web` flag: web_search.py as fallback if local KB no match
  - Cache web results → add to local KB post-review
```

#### D4. Security Model

```
On first run:
  1. User sets passphrase
  2. System derives key via PBKDF2(passphrase, salt, 100k iterations)
  3. Knowledge base folder encrypted with AES-256-GCM
  4. Metadata encrypted + access audit log (plain text, append-only)

On subsequent runs:
  1. User enters passphrase
  2. System derives key deterministically
  3. Decrypt and load KB
  4. Audit log recorded
```

#### D5. Data Model (End State)

```
analyzer-kb/
  ├── .config/
  │   ├── analyzer.toml          (plaintext: model sizes, paths, etc.)
  │   └── .security.json.enc     (encrypted: key derivation params)
  ├── documents/
  │   ├── doc-001.md.enc         (encrypted chunks + frontmatter)
  │   └── doc-002.md.enc
  ├── vectors/
  │   ├── embeddings.faiss       (binary FAISS index)
  │   ├── metadata.json          (chunk IDs, sources, dates, costs)
  │   └── chunk-map.json         (doc ID → chunks)
  ├── models/
  │   ├── distiluse-base/        (embeddings model cache)
  │   └── llm-7b-quantized/      (optional local LLM)
  ├── audit.log                  (plaintext append-only: user access)
  └── .index-meta.json           (SHA256 hashes per document)
```

#### D6. Polito Integration

**Metadata Convention** (added to YAML frontmatter of chunks):
```yaml
---
source: "01_Embedded_Systems_Lecture_01.pdf"
course: "ELC-MSc-2024"
academic_year: 2024
lecturer: "Prof. XYZ"
lesson: 1
language: "it"
content_type: "lecture_slide | lecture_note | student_exercise | solution"
extracted_at: 2026-03-18T10:30:00Z
---
```

This allows filtering/ranking results by course/lecturer/content type.

---

## Relevant Files (Immediate Changes)

| File | Changes |
|------|---------|
| [setup.ps1](../setup.ps1) | Risoluzione interprete robusta, validazione pip, fail-fast, diagnostica |
| [setup.sh](../setup.sh) | Coerenza interprete, validazione pip, esclusione MSYS2 |
| [README.md](../README.md) | Sezione PATH Windows/Linux/macOS, troubleshooting Python PATH |
| [requirements.txt](../requirements.txt) | (no change) |
| [src/analyzer.py](../src/analyzer.py) | (smoke test) |
| [src/pdf_analyzer.py](../src/pdf_analyzer.py) | (reused in D1) |
| [src/video_transcriber.py](../src/video_transcriber.py) | (reused in D1) |
| [src/web_search.py](../src/web_search.py) | (fallback opzionale) |

---

## Verification Checklist

- [ ] Windows: `where python`, `py -0p`, `py -3 -m pip --version`
- [ ] Windows: `.\setup.ps1` completa senza "No module named pip"
- [ ] Windows: `python -m pip show PyMuPDF openai-whisper pytesseract duckduckgo-search pillow`
- [ ] Windows: `python src/analyzer.py --help` funziona
- [ ] Windows: `python src/analyzer.py search "test" --n 1` funziona
- [ ] Linux/macOS: `which -a python3 python`, `python3 -m pip --version`
- [ ] Linux/macOS: `bash setup.sh` completa senza errori pip
- [ ] Linux/macOS: smoke test CLI
- [ ] ffmpeg: `ffmpeg -version` nel PATH
- [ ] Tesseract: `tesseract --version` nel PATH
- [ ] README aggiornato con PATH + troubleshooting

---

## Timeline (Proposed)

| Week | Phase | Deliverable |
|------|-------|-------------|
| 1 | A+B | Fixed setup.ps1/sh + updated README + verified CI |
| 2 | D1 prep | config.py + normalize.py + project structure |
| 3–5 | D1 core | chunker.py + indexer.py + retriever.py |
| 6 | D1 RAG | rag_chat.py + local Ollama integration |
| 7 | D4 security | security.py + passphrase + AES-256 |
| 8–9 | D2 testing | Unit tests + e2e test PDF/video/search → RAG |
| 10–11 | D6 Polito | Metadata schema + sample course KB |
| 12 | D3+D5 | Offline-first + sync prep |

---

## Open Questions (for refinement)

1. **Primary users**: Self-directed students? MSc-level engineers? Both?
2. **Initial KB size**: Start with 1–2 courses (500MB), or larger corpus?
3. **LLM selection**: Ollama (managed) vs. llama.cpp (lightweight) vs. both?
4. **Embedding model**: `distiluse-base-multilingual-cased-v2` (600MB, 1GB VRAM) or smaller?
5. **Microcontroller timeline**: Phase 6 (12+ months) or accelerated?
6. **Fine-tuning**: Out of scope, or Phase 7+?
7. **Commercial intent**: Hobby tool, or product requiring PyMuPDF license audit?

---

## Next Action

**Approved**:
1. ✅ Implement Phase A (setup.ps1/sh hardening)
2. ✅ Implement Phase B (README PATH + troubleshooting)
3. ✅ Execute Phase C (verification on Windows + Linux)
4. 📋 Schedule Phase D (RAG MVP roadmap + architecture detail)

---

**See also**: 
- [README.md](../README.md) - Installation & usage guide
- `.instructions.md` - Agent behavior (coming)
- `AGENTS.md` - Custom agent profiles (coming)
