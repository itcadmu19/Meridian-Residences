# Meridian Residences Frontend

React + Vite frontend for Meridian Residences.

## Features

- Dashboard matching the Meridian luxury SaaS design
- My Lease / User Story 1
- Shared sidebar and navbar
- Responsive layout
- Axios service layer
- FastAPI-ready API integration
- Demo fallback when backend is unavailable
- High-resolution external building/interior imagery
- No hard-coded resident name such as "Anu"

## Run

```bash
npm install
npm run dev
```

Open:

http://localhost:5173

## Backend

Create `.env`:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

Expected lease endpoints:

- GET `/leases/{id}`
- GET `/guests/{id}/leases`
- GET `/leases/{id}/summary`

The UI falls back to demo data if the FastAPI server is not running.

## Images

Dashboard hero is a 4-photo cross-fade slideshow (all real photographs, no
renders), cycling every 5 seconds:
- Montreux, Switzerland: https://unsplash.com/photos/modern-apartment-buildings-with-balconies-and-palm-trees-aAqVluPj-Sk
- Verona, Italy: https://unsplash.com/photos/colorful-european-buildings-with-flower-filled-balconies-mfQf0XfSn7k
- Palm-tree tower: https://unsplash.com/photos/modern-skyscraper-with-balconies-and-palm-trees-under-blue-sky-Iqho3mSKg6I
- Tehran, Iran: https://unsplash.com/photos/modern-apartment-building-with-balconies-against-blue-sky-_YhTiNAk_vQ

Dashboard welcome/interior image (real photo, no people, Pexels):
https://www.pexels.com/photo/spacious-modern-luxury-apartment-in-minimalistic-style-7214456/

My Lease property image (real photo, Verona, Italy - same as one of the
Dashboard slides, kept distinct from the others):
https://unsplash.com/photos/colorful-european-buildings-with-flower-filled-balconies-mfQf0XfSn7k

Several earlier candidates were rejected after downloading and inspecting
them: at least two turned out to be 3D architectural renders despite being
labeled "photo" on their source page, and one interior candidate had a
person visible in frame. All source pages identify the images as free to
use under their respective license. Check current licensing before final
commercial deployment.