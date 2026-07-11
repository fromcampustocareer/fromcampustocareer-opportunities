# Contributing to From Campus to Career

Thank you for your interest in contributing! This repository is a single, community-curated list of opportunities that help college students go **from campus to career**.

## How to Add an Opportunity

### Just Paste the Link! (Recommended)

The easiest way to contribute:

1. Go to **Issues** → **New Issue**
2. Select **"Add Opportunity (Just Paste Link)"**
3. Paste the URL to the opportunity
4. Submit!

**That's it!** AI will automatically extract:
- Organization name
- Opportunity title
- Location
- Type (Internship / Program / Research / Scholarship / etc.)
- Deadline
- Season
- Sponsorship info

### Alternative Methods

| Template | When to Use |
|----------|-------------|
| **Just Paste Link** | Default - paste URL, AI extracts everything |
| **Quick Add** | If AI extraction fails, manually fill a few fields |
| **New Opportunity** | Want full control over all details |

---

## What Qualifies?

Anything that helps a college student move toward a career: internships, fellowships, externships, programs, research, scholarships, conferences, mentorship, and early-career pipelines.

Opportunities are grouped into **industry sections** (Investment Banking, Quant Trading, Big Tech, AI, and so on), generated automatically from each listing's `industry` field. Within a section, the **Type** column tells readers what kind of opportunity it is. If a submission's industry isn't set, it lands under **Other** until a maintainer files it.

### Guidelines

- **Search existing issues** before submitting to avoid duplicates
- **Use official links** — no referral links or affiliate URLs
- Be respectful and help maintain accurate information

---

## Closing an Opportunity

### Closing (Application No Longer Open)

1. Go to **Issues** → **New Issue**
2. Select **Close Opportunity**
3. Provide the organization name and opportunity title
4. Submit

### Editing (Information Changed)

Editing via issues is not currently supported. To update a listing:
1. Open a **Close Opportunity** issue to remove the old listing
2. Open a new **Add Opportunity** issue with the corrected details

---

## How the Automation Works

1. **User submits** a link via the issue template
2. **Maintainer reviews** and adds the `approved` label
3. **AI extracts** organization, title, location, type, etc. from the page
4. **Automation adds** the opportunity to the table
5. **Issue is closed** with a summary of what was added

`listings.json` is the single source of truth — the README's per-industry tables are auto-generated from it by `update_readmes.py`.

---

Thank you for helping students find great opportunities!
