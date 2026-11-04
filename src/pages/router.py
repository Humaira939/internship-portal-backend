"""Serves the frontend pages from FastAPI, so the address bar shows /login and not login.html.
 
  route  = URL path + a function that returns the HTML page      (/login  ->  html/login.html)
  The file name stays inside the server; the browser only sees the route.
 
  Also done here:
    - /css, /js and /images are served as static folders (the pages use ../css/..., ../js/...)
    - an old link like /login.html is redirected to /login (so nothing breaks while the links are cleaned)
"""
from pathlib import Path
 
from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
 
from src.pages.discovery import discover_pages, template_conflicts
from src.utils.settings import settings
 
class RevalidatingStaticFiles(StaticFiles):
    """Static files (css, js, images) that the browser must re-check on every load.
 
    Without this the browser may keep an old copy of a css/js file for a long time and a change made by the
    frontend member does not show. With "no-cache" the browser still keeps the file, but asks the server
    first (ETag); if the file did not change the answer is a tiny 304, if it changed the new file is sent."""
 
    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "no-cache"
        return response
 
 
PROJECT_ROOT = Path(__file__).resolve().parents[2]      # the folder that contains src/
ASSET_FOLDERS = ("css", "js", "images")
 
 
def frontend_dir() -> Path:
    """FRONTEND_DIR from .env. A relative path is read from the backend project folder."""
    path = Path(getattr(settings, "FRONTEND_DIR", "../SmartIntern-fyp/internship-portal-frontend"))
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()
 
 
def setup_frontend(app: FastAPI):
    """Called once from main.py. If anything is missing it only prints a message: the API keeps working."""
    folder = frontend_dir()
    html_dir = folder / "html"
 
    pages = discover_pages(html_dir)
    if not pages:
        print(f"[pages] No frontend pages found in: {html_dir}")
        print("[pages] Set FRONTEND_DIR in .env to the internship-portal-frontend folder. The API still works.")
        return
 
    try:
        from fastapi.templating import Jinja2Templates
        templates = Jinja2Templates(directory=str(html_dir))
    except Exception as error:      # jinja2 not installed
        print(f"[pages] Pages are off: {error}. Run:  pip install jinja2")
        return
 
    for filename in template_conflicts(html_dir, pages):
        print(f"[pages] WARNING: {filename} contains {{{{ or {{% or {{# which Jinja2 reads as template code.")
 
    def render(request: Request, filename: str):
        try:
            response = templates.TemplateResponse(request=request, name=filename)        # newer Starlette
        except TypeError:
            response = templates.TemplateResponse(filename, {"request": request})       # older Starlette
        response.headers["Cache-Control"] = "no-cache"      # a changed page shows on the next reload
        return response
 
    router = APIRouter()
 
    def make_page(filename: str):
        def page(request: Request):
            return render(request, filename)
        return page
 
    for route, filename in pages.items():
        router.add_api_route(route, make_page(filename), methods=["GET"], include_in_schema=False)
 
    # Old links: /login.html  ->  /login   (keeps ?id=7 and similar)
    known = {filename[:-5] for filename in pages.values()}
 
    @router.get("/{name}.html", include_in_schema=False)
    def old_html_link(name: str, request: Request):
        if name not in known:
            raise HTTPException(status_code=404, detail="Page not found")
        target = "/" if name == "index" else f"/{name}"
        if request.url.query:
            target += f"?{request.url.query}"
        return RedirectResponse(target, status_code=301)
 
    app.include_router(router)
 
    for asset in ASSET_FOLDERS:
        asset_dir = folder / asset
        if asset_dir.is_dir():
            app.mount(f"/{asset}", RevalidatingStaticFiles(directory=str(asset_dir)), name=asset)
        else:
            print(f"[pages] Folder not found, skipped: {asset_dir}")
 
    print(f"[pages] {len(pages)} pages served from {folder}")