from flask import Flask, request, send_file, render_template_string
import requests
from io import BytesIO
import os

app = Flask(__name__)

API = os.environ.get("API")
URL = os.environ.get("URL")

README_PROMPT = """
You are an expert at creating professional, eye-catching README.md files for GitHub projects.

Generate a README in Markdown format based on the following inputs. If any fields are missing or empty, skip them or generate reasonable defaults.

- Project Name: {name}
- Description: {desc}
- Features: {features}
- Installation: {install}
- Usage: {usage}

Include:
- A header with the project name, tagline, and badges (MIT license, stars, build status from shields.io)
- A fun intro section
- A features table with emojis (if features provided)
- Installation and usage sections with code blocks (if provided)
- 'Why Use It?' bullets
- 'Contributing' section
- Playful footer with social links placeholder

Use clear headings, clean Markdown, and plenty of emojis (🚀✨🔧🌟).
"""

def gen(name, desc, features, install, usage):
    prompt = README_PROMPT.format(
        name=name or "Unnamed Project",
        desc=desc or "No description provided.",
        features=features or "",
        install=install or "",
        usage=usage or ""
    )
    headers = {
        "Authorization": f"Bearer {API}",
        "Content-Type": "application/json",
        "HTTP-Referer": request.host_url, 
        "X-Title": "README Generator",
    }
    payload = {
        "model": "meta-llama/llama-3.1-8b-instruct:free",
        "messages": [
            {"role": "system", "content": "You are a creative README generator."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1500,
        "temperature": 0.7
    }

    try:
        response = requests.post(URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError as e:
        return f"HTTP Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"Unexpected Error: {str(e)}"

HTML_TEMP = """
<!DOCTYPE html>
<html>
<head>
    <title>ReadmeRiser</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; padding: 40px; }
        .container { max-width: 800px; }
        .form-control, .btn { border-radius: 8px; }
        .preview-box { background-color: #f6f6f6; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-top: 20px; }
        .preview-box pre { background-color: #2d2d2d; color: #f8f9fa; padding: 15px; border-radius: 6px; white-space: pre-wrap; max-height: 400px; overflow-y: auto; }
        .error { color: #dc3545; font-weight: bold; }
        h1 { color: #0d6efd; font-weight: bold; }
        .btn-primary { background-color: #0d6efd; border: none; }
        .btn-success { background-color: #198754; border: none; }
        .btn-copy { background-color: #6c757d; color: white; border: none; margin-left: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="text-center mb-4">README Generator 🚀</h1>
        <p class="text-center text-muted mb-4">Craft a cool, detailed README.md with Python</p>

        <form method="POST" action="/">
            <div class="mb-3">
                <input type="text" name="name" class="form-control" placeholder="Project Name" required>
            </div>
            <div class="mb-3">
                <textarea name="desc" class="form-control" placeholder="Short Description" rows="3" required></textarea>
            </div>
            <div class="mb-3">
                <input type="text" name="features" class="form-control" placeholder="Features (comma-separated)">
            </div>
            <div class="mb-3">
                <input type="text" name="install" class="form-control" placeholder="Installation Instructions">
            </div>
            <div class="mb-3">
                <input type="text" name="usage" class="form-control" placeholder="Usage Instructions">
            </div>
            <button type="submit" class="btn btn-primary w-100">Generate README</button>
        </form>

        <!-- Loading spinner -->
        <div id="loading" class="text-center mt-4" style="display: none;">
            <div class="spinner-border text-primary" role="status"></div>
            <p class="mt-2">Generating your awesome README... ✨</p>
        </div>

        {% if preview %}
            <div class="preview-box mt-4">
                <h3>Preview</h3>
                <div class="d-flex justify-content-between align-items-center">
                    <small class="text-muted">Markdown Preview</small>
                    <button class="btn btn-copy btn-sm" onclick="copyToClipboard()">📋 Copy</button>
                </div>
                <pre id="markdownPreview"><code>{{ preview }}</code></pre>
                <form method="POST" action="/download">
                    <input type="hidden" name="readme_content" value="{{ readme_content | e }}">
                    <button type="submit" class="btn btn-success mt-3">⬇️ Download README.md</button>
                </form>
            </div>
        {% endif %}
        {% if error %}
            <p class="error mt-3">{{ error }}</p>
        {% endif %}
    </div>

    <script>
        document.querySelector("form").addEventListener("submit", function () {
            document.getElementById("loading").style.display = "block";
        });

        function copyToClipboard() {
            const markdown = document.getElementById("markdownPreview").innerText;
            navigator.clipboard.writeText(markdown).then(() => {
                alert("Copied to clipboard!");
            });
        }
    </script>
    <footer class="text-center mt-5 text-muted">
    <hr>
    <p>Made with ❤️ by Shelby</p>
    <p>
        <a href="https://github.com/whoshelby/README-Generator" target="_blank">🌐 View Source on GitHub</a> • 
        <a href="https://github.com/whoshelby" target="_blank">👨‍💻 by Shelby</a>
    </p>
    </footer>

</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    preview = None
    readme_content = None
    error = None

    if request.method == "POST":
        project_name = request.form.get("name", "").strip()
        desc = request.form.get("desc", "").strip()
        features = request.form.get("features", "").strip()
        install = request.form.get("install", "").strip()
        usage = request.form.get("usage", "").strip()

        readme_content = gen(project_name, desc, features, install, usage)

        if "Error" in readme_content:
            error = readme_content
        else:
            preview = readme_content

    return render_template_string(HTML_TEMP, preview=preview, readme_content=readme_content, error=error)

@app.route("/download", methods=["POST"])
def download():
    readme_content = request.form["readme_content"]
    readme_bytes = BytesIO(readme_content.encode("utf-8"))
    return send_file(
        readme_bytes,
        mimetype="text/markdown",
        as_attachment=True,
        download_name="README.md"
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000)) 
    app.run(host="0.0.0.0", port=port, debug=False)
