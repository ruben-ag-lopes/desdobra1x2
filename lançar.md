terminais separados:

Terminal 1 — Backend:

cd C:\Users\HP\Desktop\games_generator\backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
Terminal 2 — Frontend:

cd C:\Users\HP\Desktop\games_generator\frontend
npm run dev
Depois abre http://localhost:5173 no browser.