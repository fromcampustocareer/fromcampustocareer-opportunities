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
# alphabetically after these, and "Other" is always shown last. The canonical
# list lives in util so the contribution scripts classify against the same one.
INDUSTRY_ORDER = util.INDUSTRIES

HEADER = "| Status | Organization | Opportunity | Type | Location | Application | Date Posted |"
SEPARATOR = "| ------ | ------------ | ----------- | ---- | -------- | ----------- | ----------- |"


def gh_slug(text):
    """Approximate GitHub's heading-anchor slug for in-page links."""
    slug = text.strip().lower()
    slug = re.sub(r"[^a-z0-9 \-]", "", slug)
    return slug.replace(" ", "-")


def render_row(listing, today=None):
    """Render one listing as a markdown table row (identical style across tables)."""
    today = today or datetime.now(util.PST)
    active = listing.get("active", True)
    if not active:
        status = "🔒 **[CLOSED]**"
    elif util.is_opens_soon(listing, today):
        # Applications have not opened yet -- an `opens_on` date in the future.
        status = "⏳ **[OPENS SOON]**"
    else:
        status = "✅ **[OPEN]**"

    org = util.sanitize_table_cell(listing["company_name"])

    title = util.sanitize_table_cell(listing["title"])
    title += util.get_sponsorship_badge(listing.get("sponsorship", ""))
    title += util.get_status_badge(active)

    opp_type = util.sanitize_table_cell(listing.get("opportunity_type", ""))
    location = util.format_locations(listing.get("locations", []))
    link = util.format_link(listing["url"]) if active else ":lock:"
    date = util.format_date(listing["date_posted"])

    return f"| {status} | {org} | {title} | {opp_type} | {location} | {link} | {date} |"


def create_grouped_tables(listings, today=None):
    """Group listings by industry and render a section (header + table) per industry."""
    today = today or datetime.now(util.PST)
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
        rows = util.sort_listings(groups[industry], today)
        count = len(rows)
        out.append(f"### {industry}")
        out.append("")
        out.append(f"**{count} open role{'s' if count != 1 else ''}**")
        out.append("")
        out.append(HEADER)
        out.append(SEPARATOR)
        for listing in rows:
            out.append(render_row(listing, today))
        out.append("")

    return "\n".join(out).rstrip()


def main():
    try:
        listings = util.get_listings_from_json()
        util.check_schema(listings)

        now = datetime.now(util.PST)
        visible = [l for l in listings if l.get("is_visible", True)]
        table = create_grouped_tables(visible, now)

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

        timestamp = now.strftime("%Y-%m-%d %H:%M PST")
        util.set_output("commit_message", f"Update README ({timestamp})")

        active = sum(1 for l in visible if l.get("active", True))
        opens_soon = sum(1 for l in visible if util.is_opens_soon(l, now))
        closing = sum(1 for l in visible
                      if l.get("active", True) and util.is_closing_soon(l, now))
        industries = len({l.get("industry") or "Other" for l in visible})
        print(f"Successfully updated README: {len(visible)} opportunities "
              f"({active} active, {closing} closing soon, {opens_soon} opens soon) "
              f"across {industries} industries")

    except Exception as e:
        util.fail(str(e))


if __name__ == "__main__":
    main()
