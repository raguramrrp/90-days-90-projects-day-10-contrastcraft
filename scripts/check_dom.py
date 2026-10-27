import re
from pathlib import Path

html = Path("d:/90 days/90-days-90-projects-day-10-contrastcraft/frontend/index.html").read_text(encoding="utf-8")
js = Path("d:/90 days/90-days-90-projects-day-10-contrastcraft/frontend/js/app.bundle.js").read_text(encoding="utf-8")

html_ids = set(re.findall(r'id=["\']([^"\']+)["\']', html))
js_ids = set(re.findall(r'getElementById\(["\']([^"\']+)["\']', js))

print("Total HTML IDs:", len(html_ids))
print("Total JS getElementById IDs:", len(js_ids))
missing = js_ids - html_ids
print("Missing IDs in HTML:", missing)
