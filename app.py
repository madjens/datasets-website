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
    host, user, pw = map(os.getenv, ["SMTP_HOST", "SMTP_USER", "SMTP_PW"])
    to_addr = os.getenv("ADMIN_EMAIL", user)
    if not all([host, user, pw, to_addr]):
        app.logger.info("Email not sent (SMTP not configured). Body:\n%s", body)
        return
    with smtplib.SMTP_SSL(host, 465) as s:
        s.login(user, pw)
        s.sendmail(user, [to_addr], f"Subject: New dataset submission\n\n{body}")

# ---------- load data ----------
with open(ROOT / "data" / "datasets.yaml", "r", encoding="utf-8") as f:
    DATASETS = yaml.safe_load(f)

INTRO_HTML = load_md("intro.md")
ABOUT_HTML = load_md("about.md")
MODALITIES = ["EEG", "MEG", "fNIRS", "Physiological"]

@app.context_processor
def inject_globals():
    return dict(MODALITIES=MODALITIES)

# ---------- routes ----------
@app.route("/")
def intro():
    return render_template("intro.html", intro_html=INTRO_HTML)

@app.route("/datasets")
def datasets():
    return render_template("datasets.html", datasets=DATASETS)

@app.route("/modality/<name>")
def modality(name):
    rows = [d for d in DATASETS if name.lower() in d["signals"].lower()]
    return render_template("modality.html", datasets=rows, modality=name.capitalize())

@app.route("/about")
def about():
    return render_template("about.html", about_html=ABOUT_HTML)

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        form = request.form
        body = f"""New Dataset Submission\n=========================\nName: {form['name']}\nLink: {form['link']}\nSignals: {form['signals']}\nSubjects / Duration: {form['meta']}\nSuggested tasks: {form.get('tasks')}\nContact email: {form['email']}\nDescription: {form['description']}\n"""
        send_email(body)
        flash("Thanks! Your dataset was submitted; we’ll review it soon.")
        return redirect(url_for("contact"))
    return render_template("contact.html")

if __name__ == "__main__":
    app.run(debug=True)