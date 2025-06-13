from flask import Flask, render_template, request
import yaml, markdown, os, pathlib

ROOT = pathlib.Path(__file__).parent

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-key-change-me")

# ---------- constants ----------
GOOGLE_FORM_EMBED = os.getenv(
    "GOOGLE_FORM_EMBED",
    "https://docs.google.com/forms/d/e/1FAIpQLSe-HbKmth8ARJY1nx_1griLefuUPOYTkNYVfK3f5xab26qgPQ/viewform?embedded=true",  
)

# ---------- helpers ----------

def load_md(fname: str) -> str:
    f = ROOT / "content" / fname
    return markdown.markdown(f.read_text(encoding="utf-8"), extensions=["fenced_code", "tables"])

# ---------- load data ----------
with open(ROOT / "data" / "datasets.yaml", "r", encoding="utf-8") as f:
    DATASETS = yaml.safe_load(f)

INTRO_HTML = load_md("intro.md")
ABOUT_HTML = load_md("about.md")

ALL_MODALITIES = sorted({sig.strip() for d in DATASETS for sig in d["signals"].split("+")})
ALL_TASKS = sorted({t for d in DATASETS for t in d["tasks"]})

# ---------- routes ----------
@app.route("/")
def intro():
    return render_template("intro.html", intro_html=INTRO_HTML)

@app.route("/datasets")
def datasets():
    return render_template(
        "datasets.html",
        datasets=DATASETS,
        modalities=ALL_MODALITIES,
        tasks=ALL_TASKS,
        stimtypes=ALL_STIMTYPES,
        filter_label=None,
    )

@app.route("/modality/<name>")
def modality(name):
    rows = [d for d in DATASETS if name.lower() in d["signals"].lower()]
    return render_template(
        "datasets.html",
        datasets=rows,
        modalities=ALL_MODALITIES,
        tasks=ALL_TASKS,
        stimtypes=ALL_STIMTYPES,
        filter_label=f"Modality: {name.upper()}",
    )

@app.route("/task/<task>")
def task(task):
    rows = [d for d in DATASETS if task in d["tasks"]]
    return render_template(
        "datasets.html",
        datasets=rows,
        modalities=ALL_MODALITIES,
        tasks=ALL_TASKS,
        stimtypes=ALL_STIMTYPES,
        filter_label=f"Task: {task.replace('_',' ').title()}",
    )

@app.route("/about")
def about():
    return render_template("about.html", about_html=ABOUT_HTML)

@app.route("/contact")
def contact():
    # simply render the Google Form iframe
    return render_template("contact.html", form_embed=GOOGLE_FORM_EMBED)

ALL_STIMTYPES = sorted({d["stimulus_type"] for d in DATASETS})

@app.route("/stimulus/<stype>")
def stimulus(stype):
    rows = [d for d in DATASETS if d["stimulus_type"] == stype]
    return render_template(
        "datasets.html",
        datasets=rows,
        modalities=ALL_MODALITIES,
        tasks=ALL_TASKS,
        stimtypes=ALL_STIMTYPES,
        filter_label=f"Stimulus: {stype}",
    )
    
if __name__ == "__main__":
    app.run(debug=True)