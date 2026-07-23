#!/usr/bin/env python3
"""
Update README.md with the latest listings from listings.json.

Opportunities are grouped into industry sections (one markdown table per
industry), generated from each listing's `industry` field and embedded in the
README between the marker comments. Ordering of sections is defined by
INDUSTRY_ORDER; any unknown industry is appended alphabetically, with "Other"
last.
"""

import os
import re
from datetime import datetime
import util


# Display order of industry sections. Unknown industries are appended
# alphabetically after these, and "Other" is always shown last.
INDUSTRY_ORDER = [
    "Investment Banking & Financial Services",
    "Quant Trading, Hedge Funds & Market Making",
    "Big Tech & Enterprise Software",
    "AI, ML & Software Startups",
    "Fellowships, Scholarships & Career Programs",
    "Industrial, Energy & Manufacturing",
    "Aerospace, Defense & National Labs",
    "Asset Management & Venture Capital",
    "Semiconductors & Hardware",
    "Healthcare & Medical Devices",
    "Medical & Health-Field Opportunities for Students",
    "Consumer & Food",
]

HEADER = "| Status | Organization | Opportunity | Type | Location | Application | Date Posted |"
SEPARATOR = "| ------ | ------------ | ----------- | ---- | -------- | ----------- | ----------- |"


def gh_slug(text):
    """Approximate GitHub's heading-anchor slug for in-page links."""
    slug = text.strip().lower()
    slug = re.sub(r"[^a-z0-9 \-]", "", slug)
    return slug.replace(" ", "-")


def render_row(listing):
    """Render one listing as a markdown table row (identical style across tables)."""
    active = listing.get("active", True)
    status = "✅ **[OPEN]**" if active else "🔒 **[CLOSED]**"

    org = util.sanitize_table_cell(listing["company_name"])

    title = util.sanitize_table_cell(listing["title"])
    title += util.get_sponsorship_badge(listing.get("sponsorship", ""))
    title += util.get_status_badge(active)

    opp_type = util.sanitize_table_cell(listing.get("opportunity_type", ""))
    location = util.format_locations(listing.get("locations", []))
    link = util.format_link(listing["url"]) if active else ":lock:"
    date = util.format_date(listing["date_posted"])

    return f"| {status} | {org} | {title} | {opp_type} | {location} | {link} | {date} |"


def create_grouped_tables(listings):
    """Group listings by industry and render a section (header + table) per industry."""
    groups = {}
    for listing in listings:
        industry = listing.get("industry") or "Other"
        groups.setdefault(industry, []).append(listing)

    order = [i for i in INDUSTRY_ORDER if i in groups]
    order += sorted(k for k in groups if k not in INDUSTRY_ORDER and k != "Other")
    if "Other" in groups:
        order.append("Other")

    out = []
    out.append(f"**{len(listings)} open roles across {len(order)} industries.** Jump to a sector:")
    out.append("")
    for industry in order:
        out.append(f"- [{industry}](#{gh_slug(industry)}) — {len(groups[industry])}")
    out.append("")

    for industry in order:
        rows = util.sort_listings(groups[industry])
        count = len(rows)
        out.append(f"### {industry}")
        out.append("")
        out.append(f"**{count} open role{'s' if count != 1 else ''}**")
        out.append("")
        out.append(HEADER)
        out.append(SEPARATOR)
        for listing in rows:
            out.append(render_row(listing))
        out.append("")

    return "\n".join(out).rstrip()


def main():
    try:
        listings = util.get_listings_from_json()
        util.check_schema(listings)

        visible = [l for l in listings if l.get("is_visible", True)]
        table = create_grouped_tables(visible)

        readme_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "..",
            "README.md"
        )

        util.embed_table(
            readme_path,
            table,
            "<!-- OPPORTUNITIES_TABLE_START -->",
            "<!-- OPPORTUNITIES_TABLE_END -->"
        )

        now = datetime.now(util.PST)
        timestamp = now.strftime("%Y-%m-%d %H:%M PST")
        util.set_output("commit_message", f"Update README ({timestamp})")

        active = sum(1 for l in visible if l.get("active", True))
        industries = len({l.get("industry") or "Other" for l in visible})
        print(f"Successfully updated README: {len(visible)} opportunities "
              f"({active} active) across {industries} industries")

    except Exception as e:
        util.fail(str(e))


if __name__ == "__main__":
    main()
