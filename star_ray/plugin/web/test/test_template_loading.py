from importlib.resources import files
from pathlib import Path
from fastapi.templating import Jinja2Templates

# Access the directory as a Path object
static_js_dir = files("star_ray_web").joinpath("static/js")

# List JavaScript files; note that this approach requires Python >= 3.10
# For older versions, you might need to convert it to a Path object or adjust your approach
javascript_files = [file.name for file in static_js_dir.iterdir() if file.is_file()]
for file_name in javascript_files:
    name = Path(file_name).stem
    path = static_js_dir.joinpath(file_name)
    print(name, path)

# Accessing the templates directory
template_dir = files("star_ray_web").joinpath("templates")

# Converting to a string path if needed (e.g., for APIs expecting string paths)
template_dir_str = str(template_dir)

print(template_dir_str)

templates = Jinja2Templates(directory=template_dir_str)
