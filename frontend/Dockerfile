# Runs the existing Vite dev server, not a production Nginx build - this
# project has no production build/serve setup today (no nginx.conf, no
# static-hosting config anywhere in the repo), and Dockerization's job is
# to containerize what already exists, not introduce a new deployment
# architecture. `npm run dev` + vite.config.js's `host: true` (see that
# file) is the direct container equivalent of how this app already runs
# locally, so behavior (HMR, etc.) stays identical to non-Docker dev.

FROM node:20-slim

WORKDIR /app

# Installed separately from the rest of the source so this layer only
# rebuilds when package.json/package-lock.json actually change, not on
# every source edit.
COPY package.json package-lock.json ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
