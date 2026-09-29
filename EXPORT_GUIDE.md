# MonsoonLens source-code archive

This archive contains the React frontend, FastAPI backend, bundled geographic data, dependency manifests and lockfiles, tests, scripts, and product documentation.

Private `.env` files, installed dependencies, Git history, generated build files, caches, and test-output artifacts are intentionally excluded.

## Local configuration

1. Extract the archive.
2. Copy `backend/.env.example` to `backend/.env`.
3. Copy `frontend/.env.example` to `frontend/.env`.
4. Install backend dependencies in a Python 3.11 virtual environment using `pip install -r requirements.txt` from the `backend` directory. The requirements record the development environment, including some optional platform packages.
5. Install frontend dependencies with `yarn` from the `frontend` directory.
6. Run the backend from its directory with `uvicorn server:app --host 0.0.0.0 --port 8001`, and run `yarn start` from the frontend directory in a separate terminal.

See `README.md` for the product architecture, API contract, data provenance, and scientific caveats. The included historical district boundaries are already prepared; they do not need to be regenerated.

## Data and live connection

All demonstration products are synthetic. No rainfall ML model is trained. Live mode remains unavailable until the external service URL, authentication specification and response schema are supplied.

Review the geographic source terms in `backend/data/README.md` before redistribution or non-prototype use.