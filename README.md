# Darshit Joshi Resume

LaTeX resume template based on Awesome CV.

## Folder Structure

```
darshit_joshi_resume/
├── cv/                 # CV sections
├── resume/             # Resume sections  
├── fonts/              # Font files
├── templates/          # HTML templates
├── awesome-cv.cls      # LaTeX class file
├── resume.tex          # Main resume file
├── cv.tex              # Main CV file
├── coverletter.tex     # Cover letter file
└── app.py              # Flask app
```

## Generate PDF

### Requirements
- TeX Live distribution
- XeLaTeX compiler

### Steps
1. Install TeX Live: `sudo apt-get install texlive-full`
2. Compile resume: `xelatex resume.tex`
3. Output: `resume.pdf`

### Quick Start
```bash
# Clone and navigate
cd darshit_joshi_resume

# Generate PDF
xelatex resume.tex
```