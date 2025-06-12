from flask import Flask, render_template, request, redirect, url_for, flash
import yaml, markdown, os, smtplib, pathlib

ROOT = pathlib.Path(__file__).parent

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-key-change-me")

# ---------- helpers ----------

def load_md(fname: str) -> str:
    """Read Markdown & convert to HTML (string)."""
    f = ROOT / "content" / fname
    return markdown.markdown(f.read_text(encoding="utf-8"), extensions=["fenced_code", "tables"])


def send_email(body: str):
    """Send submission email or log if SMTP not configured."""
    host, user, pw = map(os.getenv, ["SMTP_HOST", "SMTP_USER", "SMTP_PW"])
    to_addr = os.getenv("ADMIN_EMAIL", user)
    if not all([host, user, pw, to_addr]):
        app.logger.info("[SUBMISSION]\n%s", body)
        return
    with smtplib.SMTP_SSL(host, 465) as s:
        s.login(user, pw)
        s.sendmail(user, [to_addr], f"Subject: New dataset submission\n\n{body}")

# ---------- load data ----------
with open(ROOT / "data" / "datasets.yaml", "r", encoding="utf-8") as f:
    DATASETS = yaml.safe_load(f)

INTRO_HTML = load_md("intro.md")
ABOUT_HTML = load_md("about.md")

# collect unique modalities & tasks (sets → sorted lists)
ALL_MODALITIES = sorted({sig.strip().split(" ")[0] for d in DATASETS for sig in d["signals"].split("+")})
ALL_TASKS = sorted({t for d in DATASETS for t in d["tasks"]})

@app.context_processor
def inject_globals():
    return dict()

# ---------- routes ----------
@app.route("/")
def intro():
    return render_template("intro.html", intro_html=INTRO_HTML)

@app.route("/datasets")
def datasets():
    return render_template("datasets.html", datasets=DATASETS, modalities=ALL_MODALITIES, tasks=ALL_TASKS, filter_label=None)

@app.route("/modality/<name>")
def modality(name):
    rows = [d for d in DATASETS if name.lower() in d["signals"].lower()]
    return render_template("datasets.html", datasets=rows, modalities=ALL_MODALITIES, tasks=ALL_TASKS, filter_label=f"Modality: {name.upper()}")

@app.route("/task/<task>")
def task(task):
    rows = [d for d in DATASETS if task in d["tasks"]]
    return render_template("datasets.html", datasets=rows, modalities=ALL_MODALITIES, tasks=ALL_TASKS, filter_label=f"Task: {task.replace('_',' ').title()}")

@app.route("/about")
def about():
    return render_template("about.html", about_html=ABOUT_HTML)

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        form = request.form
        body = (
            "New Dataset Submission\n=========================\n" +
            f"Name: {form['name']}\n" +
            f"Link: {form['link']}\n" +
            f"Signals: {form['signals']}\n" +
            f"Subjects / Duration: {form['meta']}\n" +
            f"Suggested tasks: {form.get('tasks')}\n" +
            f"Contact email: {form['email']}\n" +
            f"Description: {form['description']}\n"
        )
        send_email(body)
        flash("Thanks! Your dataset was submitted; we’ll review it soon.")
        return redirect(url_for("contact"))
    return render_template("contact.html")

if __name__ == "__main__":
    app.run(debug=True)