# Darshit Joshi Resume

LaTeX resume in the classic "Jake's Resume" style, edited through a small web UI.

## Folder Structure

```
darshit_joshi_resume/
├── resume.json         # Resume content (source of truth)
├── resume.tex          # Preamble / styling; inputs the generated files
├── resume/             # Generated section .tex files (don't edit by hand)
├── resume_builder.py   # resume.json -> .tex files -> resume.pdf
├── app.py              # Flask web UI
├── templates/          # Web UI page
├── cv.tex, coverletter.tex, awesome-cv.cls, cv/, fonts/   # Awesome-CV CV and cover letter
└── resume-two-column.tex
```

## Editing the resume

Requirements: a TeX Live install with XeLaTeX (`sudo apt-get install texlive-full`) and Flask.

```bash
./start.sh            # or: venv/bin/python app.py
```

Open http://localhost:5000, edit any field, and press **Save & build** (or Ctrl+S).
The content is saved to `resume.json`, the `.tex` files are regenerated, and `resume.pdf`
is rebuilt and reloaded in the preview. If LaTeX fails, the previous PDF is kept and the
error is shown under the preview.

Styling (fonts, margins, section rules) lives in the preamble of `resume.tex`.

To build without the UI: `xelatex resume.tex`.
