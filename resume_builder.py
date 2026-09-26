"""Render resume.json into the LaTeX section files and compile resume.pdf."""
import json
import os
import re
import subprocess
import threading
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'resume.json')
SECTIONS_DIR = os.path.join(BASE_DIR, 'resume')
BUILD_DIR = os.path.join(BASE_DIR, '.build')
LAST_BUILD_FILE = os.path.join(BUILD_DIR, 'last-build.json')
PDF_FILE = os.path.join(BASE_DIR, 'resume.pdf')

SECTION_IDS = ['summary', 'skills', 'projects', 'experience', 'achievements', 'education']
DEFAULT_TITLES = {
    'summary': 'Summary',
    'skills': 'Skills',
    'projects': 'Projects',
    'experience': 'Experience',
    'achievements': 'Achievements',
    'education': 'Education',
}

LINK_ICONS = {
    'globe': r'\faGlobe',
    'linkedin': r'\faLinkedin',
    'github': r'\faGithub',
    'gitlab': r'\faGitlab',
    'twitter': r'\faTwitter',
    'stackoverflow': r'\faStackOverflow',
    'medium': r'\faMedium',
    'link': r'\faLink',
}

GENERATED_NOTE = '% Generated from resume.json by resume_builder.py -- edit via the web UI.\n'

_build_lock = threading.Lock()


#-------------------------------------------------------------------------------
# DATA
#-------------------------------------------------------------------------------
def normalize(data):
    """Fill in missing keys so the renderer and UI can rely on the shape."""
    data = dict(data or {})
    header = dict(data.get('header') or {})
    for key in ('name', 'phone', 'email'):
        header.setdefault(key, '')
    header['links'] = list(header.get('links') or [])
    data['header'] = header

    data.setdefault('summary', '')
    for key in ('skills', 'projects', 'experience', 'achievements', 'education'):
        data[key] = list(data.get(key) or [])

    sections = [s for s in (data.get('sections') or []) if s.get('id') in SECTION_IDS]
    seen = {s['id'] for s in sections}
    sections += [{'id': sid, 'title': DEFAULT_TITLES[sid], 'visible': True}
                 for sid in SECTION_IDS if sid not in seen]
    data['sections'] = sections
    return data


def load():
    with open(DATA_FILE, encoding='utf-8') as f:
        return normalize(json.load(f))


def save(data):
    """Persist the data and regenerate the .tex files from it."""
    data = normalize(data)
    tmp = DATA_FILE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')
    os.replace(tmp, DATA_FILE)

    for name, content in render(data).items():
        with open(os.path.join(SECTIONS_DIR, name), 'w', encoding='utf-8') as f:
            f.write(content)
    return data


#-------------------------------------------------------------------------------
# LATEX RENDERING
#-------------------------------------------------------------------------------
_TEX_ESCAPES = {
    '\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#',
    '_': r'\_', '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}',
}
_TEX_RE = re.compile('|'.join(re.escape(c) for c in _TEX_ESCAPES))
_BOLD_RE = re.compile(r'\*\*(.+?)\*\*')


def tex(text):
    """Escape plain text for LaTeX, turning **bold** into \\textbf{bold}."""
    text = ' '.join((text or '').split())
    text = _TEX_RE.sub(lambda m: _TEX_ESCAPES[m.group()], text)
    return _BOLD_RE.sub(r'\\textbf{\1}', text)


def url(value):
    """Make a URL safe to use as an \\href target."""
    value = re.sub(r'[\s\\{}]', '', value or '')
    if value and not re.match(r'^[a-z][a-z0-9+.-]*:', value, re.I):
        value = 'https://' + value
    return value.replace('%', r'\%').replace('#', r'\#')


def _itemize(items):
    items = [tex(i) for i in items if (i or '').strip()]
    if not items:
        return ''
    return '\\begin{itemize}\n' + ''.join(f'  \\item {i}\n' for i in items) + '\\end{itemize}\n'


def _subheading(left_top, right_top, left_bottom, right_bottom):
    return (
        '\\resumeSubheading\n'
        f'  {{{tex(left_top)}}}\n  {{{tex(right_top)}}}\n'
        f'  {{{tex(left_bottom)}}}\n  {{{tex(right_bottom)}}}\n'
    )


def render_header(header):
    items = []
    if header['phone'].strip():
        tel = re.sub(r'[^\d+]', '', header['phone'])
        items.append(rf'\href{{tel:{tel}}}{{\faPhone*\ {tex(header["phone"])}}}')
    if header['email'].strip():
        email = header['email'].strip()
        items.append(rf'\href{{{url("mailto:" + email)}}}{{\faEnvelope\ \underline{{{tex(email)}}}}}')
    for link in header['links']:
        if not (link.get('url') or '').strip():
            continue
        icon = LINK_ICONS.get(link.get('icon'), LINK_ICONS['link'])
        text = tex(link.get('text') or link['url'])
        items.append(rf'\href{{{url(link["url"])}}}{{{icon}\ \underline{{{text}}}}}')

    # Each item is an unbreakable box; lines wrap between items.
    contacts = ' \\hspace{1em plus 0.5em}\n  '.join(f'\\mbox{{{i}}}' for i in items)
    return (
        GENERATED_NOTE
        + '\\begin{center}\n'
        + f'  {{\\Huge\\scshape {tex(header["name"])}}} \\\\ \\vspace{{2pt}}\n'
        + '  \\small\n'
        + f'  {contacts}\n'
        + '\\end{center}\n'
        + '\\vspace{-8pt}\n'
    )


def _render_summary(data):
    paragraphs = [tex(p) for p in re.split(r'\n\s*\n', data['summary']) if p.strip()]
    return '\n\n'.join(paragraphs) + '\n' if paragraphs else ''


def _render_skills(data):
    lines = []
    for skill in data['skills']:
        category, items = tex(skill.get('category')), tex(skill.get('items'))
        if category:
            lines.append(f'\\resumeSkill{{{category}}}{{{items}}}\n')
        elif items:
            lines.append(f'{items}\\par\n')
    return ''.join(lines)


def _render_projects(data):
    items = []
    for project in data['projects']:
        name, description = tex(project.get('name')), tex(project.get('description'))
        if not (name or description):
            continue
        if name and (project.get('url') or '').strip():
            name = rf'\href{{{url(project["url"])}}}{{\underline{{{name}}}}}'
        items.append(f'  \\item \\textbf{{{name}:}} {description}\n' if name else f'  \\item {description}\n')
    return '\\begin{itemize}\n' + ''.join(items) + '\\end{itemize}\n' if items else ''


def _render_experience(data):
    out = []
    for job in data['experience']:
        heading = [job.get(k, '') for k in ('organization', 'date', 'role', 'location')]
        if not any(h.strip() for h in heading) and not job.get('bullets'):
            continue
        out.append(_subheading(*heading) + _itemize(job.get('bullets') or []))
    return '\n'.join(out)


def _render_achievements(data):
    return _itemize(data['achievements'])


def _render_education(data):
    out = []
    for school in data['education']:
        heading = [school.get(k, '') for k in ('institution', 'date', 'degree', 'location')]
        if not any(h.strip() for h in heading) and not school.get('bullets'):
            continue
        out.append(_subheading(*heading) + _itemize(school.get('bullets') or []))
    return '\n'.join(out)


_SECTION_RENDERERS = {
    'summary': _render_summary,
    'skills': _render_skills,
    'projects': _render_projects,
    'experience': _render_experience,
    'achievements': _render_achievements,
    'education': _render_education,
}


def render(data):
    """Return {filename: contents} for every generated file in resume/."""
    files = {'header.tex': render_header(data['header'])}
    body = [GENERATED_NOTE]
    for section in data['sections']:
        sid = section['id']
        content = _SECTION_RENDERERS[sid](data)
        title = tex(section.get('title')) or DEFAULT_TITLES[sid]
        files[f'{sid}.tex'] = GENERATED_NOTE + f'\\section{{{title}}}\n\n' + content
        # Skip hidden or empty sections so no orphan heading is printed.
        if section.get('visible', True) and content.strip():
            body.append(f'\\input{{resume/{sid}.tex}}\n')
    files['body.tex'] = ''.join(body)
    return files


#-------------------------------------------------------------------------------
# BUILD
#-------------------------------------------------------------------------------
def _log_excerpt(output):
    lines = output.splitlines()
    for i, line in enumerate(lines):
        if line.startswith('!'):
            return '\n'.join(lines[i:i + 12])
    return '\n'.join(lines[-25:])


def build():
    """Compile resume.tex. The previous PDF is only replaced if the build succeeds."""
    with _build_lock:
        os.makedirs(BUILD_DIR, exist_ok=True)
        built = os.path.join(BUILD_DIR, 'resume.pdf')
        if os.path.exists(built):
            os.remove(built)

        started = time.monotonic()
        try:
            proc = subprocess.run(
                ['xelatex', '-interaction=nonstopmode', '-halt-on-error',
                 f'-output-directory={BUILD_DIR}', 'resume.tex'],
                cwd=BASE_DIR, capture_output=True, text=True, errors='replace', timeout=120,
            )
        except FileNotFoundError:
            return {'ok': False, 'error': 'xelatex is not installed or not on PATH.'}
        except subprocess.TimeoutExpired:
            return {'ok': False, 'error': 'LaTeX took longer than 2 minutes and was stopped.'}

        if proc.returncode != 0 or not os.path.exists(built):
            return {'ok': False, 'error': 'LaTeX could not compile the resume.',
                    'log': _log_excerpt(proc.stdout)}

        os.replace(built, PDF_FILE)
        pages = re.search(r'\((\d+) pages?\)', proc.stdout)
        result = {
            'ok': True,
            'seconds': round(time.monotonic() - started, 1),
            'pages': int(pages.group(1)) if pages else None,
            'built_at': time.time(),
        }
        with open(LAST_BUILD_FILE, 'w', encoding='utf-8') as f:
            json.dump(result, f)
        return result


def last_build():
    try:
        with open(LAST_BUILD_FILE, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return None
