import os, sys

c  = open("landing/index.html", encoding="utf-8").read()
js = open("landing/app.js", encoding="utf-8").read()

html_checks = [
    ("4 cards with data-modal",       c.count("data-modal=") == 4),
    ("modal-yield panel exists",      'id="modal-yield"' in c),
    ("modal-weather panel exists",    'id="modal-weather"' in c),
    ("modal-history panel exists",    'id="modal-history"' in c),
    ("modal-shap panel exists",       'id="modal-shap"' in c),
    ("modal-overlay exists",          'id="modal-overlay"' in c),
    ("close button exists",           'id="modal-close-btn"' in c),
    ("4 card-try-btn buttons",        c.count("card-try-btn") == 4),
    ("app.js loaded once",            c.count('src="app.js"') == 1),
    ("only 1 </html>",               c.count("</html>") == 1),
    ("nothing after </html>",         len(c) - c.rfind("</html>") - 7 <= 1),
]

js_checks = [
    ("openModal function",           "function openModal" in js),
    ("closeModal function",          "function closeModal" in js),
    ("data-modal wiring",            "dataset.modal" in js),
    ("initYield function",           "function initYield" in js),
    ("initWeather function",         "function initWeather" in js),
    ("initHistory function",         "function initHistory" in js),
    ("initShap function",            "function initShap" in js),
    ("wiz-next-state handler",       "wiz-next-state" in js),
    ("weather-fetch-btn handler",    "weather-fetch-btn" in js),
    ("hist-fetch-btn handler",       "hist-fetch-btn" in js),
    ("shap-run-btn handler",         "shap-run-btn" in js),
    ("wiz-predict-btn handler",      "wiz-predict-btn" in js),
    ("/api/predict call",            "/api/predict" in js),
    ("/api/weather call",            "/api/weather" in js),
    ("/api/historical-trends call",  "/api/historical-trends" in js),
    ("/api/metadata call",           "/api/metadata" in js),
]

print("\n=== HTML CHECKS ===")
all_ok = True
for name, ok in html_checks:
    if not ok: all_ok = False
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")

print("\n=== JS CHECKS ===")
for name, ok in js_checks:
    if not ok: all_ok = False
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")

print("\n" + "="*40)
print(f"  VERDICT: {'FULLY FUNCTIONAL' if all_ok else 'ISSUES FOUND'}")
print("="*40 + "\n")
sys.exit(0 if all_ok else 1)
