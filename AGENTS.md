# Repository Guidelines

## Project Structure & Module Organization
This monorepo splits the Django API under `backend/` and the Vue admin client under `frontend/`. Backend apps live in `backend/apps/{system,user,monitor,functiontest}` with reusable helpers in `backend/utils/` and shared static assets in `backend/static/`. Database seeding scripts reside in `backend/script/`, while deployment artifacts (Dockerfile, Gunicorn config, docker-compose) stay at the root of `backend/`. Frontend UI code sits in `frontend/src/` (components in `src/components/`, views in `src/views/`, state in `src/store/`), and supporting assets live in `frontend/public/`, `frontend/locales/`, and `frontend/mock/`.

## Build, Test, and Development Commands
Install backend dependencies with `cd backend && python -m pip install -r requirements.txt`. Run `python manage.py migrate` to sync the database and `python manage.py runserver 0.0.0.0:8000` for local API development. Execute `python manage.py test` or `python manage.py test apps.user` to run Django’s test suite. For the frontend, prefer pnpm: `cd frontend && pnpm install`, `pnpm dev` for hot-reload dev server, `pnpm build` for production bundles, and `pnpm lint` to run ESLint, Prettier, and Stylelint in sequence. `docker-compose -f backend/docker-compose.yml up --build` provisions the API with Gunicorn if you need a containerised check.

## Coding Style & Naming Conventions
Python code follows Black (configured line width 400) and isort; stick to snake_case modules and PascalCase class names. Django apps expose REST endpoints via DRF—mirror existing serializer/view naming when adding modules. The Vue codebase uses TypeScript, Vue SFCs, and Tailwind. Keep component files in PascalCase (e.g. `UserAudit.vue`), composables in camelCase, and SCSS utility files in kebab-case. ESLint+Prettier enforce formatting; run `pnpm lint:eslint` before committing UI changes. Stylelint targets Vue/SCSS—nest selectors conservatively.

## Testing Guidelines
Unit tests live alongside apps (`backend/apps/**/tests.py`) and should assert both success and permission-failure paths. Add factories/fixtures under `backend/script/sql` when extending seeds. Frontend automation focuses on type safety—run `pnpm typecheck` for regressions—and rely on the mock API (`frontend/mock/`) for manual UI verification. Note key manual QA steps in the PR whenever you touch high-risk flows.

## Commit & Pull Request Guidelines
Conventional commits are enforced by commitlint (`feat`, `fix`, `docs`, `test`, `refactor`, `build`, `ci`, `chore`, `revert`, etc.); example: `feat: add role assignment audit log`. Keep subject ≤108 chars and include a blank line before body text. For pull requests, provide a concise summary, link the relevant issue, list backend/frontend command outputs you ran (tests, `pnpm lint`, migrations), and attach screenshots/GIFs for UI-visible updates. Request review from both API and UI owners when changes cross the stack.
