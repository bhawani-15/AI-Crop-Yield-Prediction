# Direct entrypoint delegating to frontend/app.py
import os
import runpy

app_path = os.path.join(os.path.dirname(__file__), "frontend", "app.py")
runpy.run_path(app_path, run_name="__main__")
