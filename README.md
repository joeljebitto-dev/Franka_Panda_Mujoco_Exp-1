# Robot Arm Pick-and-Place Simulator

A MuJoCo-powered Franka Panda pick-and-place simulator with a FastAPI backend and browser control panel.

## Setup

```bash
scripts/setup.sh
```

The setup script creates `.venv`, installs the FastAPI/MuJoCo backend dependencies, installs the Vite React frontend dependencies, and creates `backend/.env` and `frontend/.env` from their examples if they are missing.

## Run

```bash
scripts/run.sh
```

Open `http://127.0.0.1:5173`.

The simulator uses the Panda assets already present in `assets/mujoco_menagerie/franka_emika_panda`.

## Project Shape

- `backend/app/config.py` loads and validates backend constants from `backend/.env`.
- `backend/app/api/` contains route schemas and separated simulation, view, and manual routers.
- `frontend/src/config/` loads Vite environment constants from `frontend/.env`.
- `frontend/src/lib/` contains API and math helpers.
- `frontend/src/hooks/` contains polling, frame refresh, manual-control, and viewport-interaction hooks.
- `frontend/src/components/` contains the React UI components.

## Controls

- Drag in the viewport to orbit the MuJoCo camera.
- Shift-drag, right-drag, or middle-drag to pan.
- Scroll or pinch over the viewport to zoom.
- Use `Pickup` or `Target` mode to drag scene markers on the table.
- Switch to `Manual` mode to drive the seven joint targets and gripper position directly.
