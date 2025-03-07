# Simple Todo App

A minimalist todo application with FastAPI backend and vanilla JavaScript frontend.

## Features

- Add new tasks
- Mark tasks as complete/incomplete
- Delete tasks
- Offline support with LocalStorage
- REST API backend

## Setup

### Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn backend.main:app --reload
```

### Frontend
```bash
# Simply serve the frontend directory
python -m http.server 3000
```

## API Endpoints

- GET `/tasks` - Get all tasks
- POST `/task` - Create new task
- PUT `/task/:id` - Update task status
- DELETE `/task/:id` - Delete task

## Known Issues

1. No data persistence on backend restart
2. No authentication/authorization
3. CORS enabled for all origins

## Future Enhancements

See [SPEC.md](SPEC.md) for planned features.
