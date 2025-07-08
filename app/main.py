from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.routers import resume, portfolio, project, auth, talent
import os

app = FastAPI()

app.include_router(resume.router)
app.include_router(portfolio.router)
app.include_router(project.router)
app.include_router(auth.router)
app.include_router(talent.router)

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

@app.get("/resume-form", response_class=HTMLResponse)
def resume_form(request: Request):
    return templates.TemplateResponse("resume_form.html", {"request": request})

@app.get("/portfolio-form", response_class=HTMLResponse)
def portfolio_form(request: Request):
    return templates.TemplateResponse("portfolio_form.html", {"request": request})

@app.get("/project-form", response_class=HTMLResponse)
def project_form(request: Request):
    return templates.TemplateResponse("project_form.html", {"request": request})

# 추후 라우터 등록 예정 