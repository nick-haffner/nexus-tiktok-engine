"""
HTTP server that serves a download page and receives images.
The download page fetches images from TikTok CDN and POSTs them back.

Usage:
    python scripts/image_receiver.py

Then the caller navigates a browser tab to http://127.0.0.1:8765/download?urls=...
The page auto-downloads all images and POSTs them back to the server.
"""

import http.server
import json
import os
import sqlite3
import sys
import urllib.parse

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(REPO_ROOT, "store", "data", "analytics", "analytics.db")

slug_cache = {}
received = 0
expected = 0


def get_slug(post_id):
    if post_id not in slug_cache:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute(
            "SELECT slug FROM nexus_post_metadata WHERE post_id = ?", (post_id,)
        ).fetchone()
        conn.close()
        slug_cache[post_id] = row[0] if row else post_id
    return slug_cache[post_id]


# Store URL data received from browser
url_data = {}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"""<html><body>
<h2>Image Receiver Ready</h2>
<p>POST URL data to /set-urls, then GET /download to start.</p>
</body></html>""")

        elif parsed.path == "/download":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            html = f"""<!DOCTYPE html>
<html><body>
<h2>Downloading Images</h2>
<div id="status">Starting...</div>
<pre id="log" style="max-height:400px;overflow:auto;font-size:11px"></pre>
<script>
const urlData = {json.dumps(url_data)};
const log = document.getElementById('log');
const status = document.getElementById('status');
let ok = 0, fail = 0;
const total = Object.values(urlData).flat().length;

async function run() {{
  for (const [pid, urls] of Object.entries(urlData)) {{
    for (let i = 0; i < urls.length; i++) {{
      try {{
        const r = await fetch(urls[i]);
        if (!r.ok) throw new Error('HTTP ' + r.status);
        const blob = await r.blob();
        const pr = await fetch('/save', {{
          method: 'POST',
          headers: {{ 'X-Post-Id': pid, 'X-Slide-Num': String(i+1), 'Content-Type': blob.type }},
          body: blob
        }});
        if (pr.ok) {{ ok++; log.textContent += 'OK ' + pid + ' slide ' + (i+1) + '\\n'; }}
        else {{ fail++; log.textContent += 'SAVE_ERR ' + pid + ' slide ' + (i+1) + '\\n'; }}
      }} catch(e) {{
        fail++;
        log.textContent += 'FAIL ' + pid + ' slide ' + (i+1) + ': ' + e.message + '\\n';
      }}
      status.textContent = ok + '/' + total + ' ok, ' + fail + ' failed';
    }}
  }}
  status.textContent = 'DONE: ' + ok + '/' + total + ' ok, ' + fail + ' failed';
  log.textContent += '\\n=== COMPLETE ===\\n';
}}
run();
</script></body></html>"""
            self.wfile.write(html.encode())

        elif parsed.path == "/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"received": received, "expected": expected}).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        global received, expected, url_data
        parsed = urllib.parse.urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        if parsed.path == "/set-urls":
            # Handle both raw JSON and form-encoded data
            try:
                url_data = json.loads(body)
            except json.JSONDecodeError:
                form_data = urllib.parse.parse_qs(body.decode())
                url_data = json.loads(form_data.get("data", ["{}"])[0])
            expected = sum(len(v) for v in url_data.values())
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Loaded {len(url_data)} posts, {expected} URLs".encode())
            print(f"  Loaded {len(url_data)} posts, {expected} URLs")
            return

        if parsed.path.startswith("/save"):
            qs = urllib.parse.parse_qs(parsed.query)
            post_id = qs.get("pid", [self.headers.get("X-Post-Id", "unknown")])[0]
            slide_num = qs.get("slide", [self.headers.get("X-Slide-Num", "1")])[0]
            content_type = self.headers.get("Content-Type", "image/jpeg")

            ext = "jpg"
            if "webp" in content_type: ext = "webp"
            elif "png" in content_type: ext = "png"

            slug = get_slug(post_id)
            slides_dir = os.path.join(REPO_ROOT, "store", "data", "posts", slug, "slides")
            os.makedirs(slides_dir, exist_ok=True)

            filepath = os.path.join(slides_dir, f"Slide {slide_num}.{ext}")
            with open(filepath, "wb") as f:
                f.write(body)

            received += 1
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b"OK")
            sys.stdout.write(f"\r  {received}/{expected} saved")
            sys.stdout.flush()
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    port = 8765
    print(f"Image receiver on http://127.0.0.1:{port}")
    server = http.server.HTTPServer(("127.0.0.1", port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\nDone. Received {received} images.")
        server.server_close()
