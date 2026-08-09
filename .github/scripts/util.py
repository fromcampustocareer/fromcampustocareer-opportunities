"""
Utility functions for managing From Campus to Career opportunity listings.
"""

import json
import os
import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

# Constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LISTINGS_FILE = os.path.join(SCRIPT_DIR, "listings.json")
README_FILE = os.path.join(SCRIPT_DIR, "..", "..", "README.md")
PST = ZoneInfo("America/Los_Angeles")

# A deadline this many days out (or fewer) counts as "closing soon". Shared by
# closing_soon.py (which sets the badge) and sort_listings (which floats those
# rows to the top of their table) so the two can never disagree.
CLOSING_SOON_DAYS = 14

# Deadlines are written into the opportunity text, e.g. "— Deadline: Jan 15, 2027".
MONTHS = (
    "January|February|March|April|May|June|July|August|September|October|November|December|"
    "Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec"
)
DATE_RE = re.compile(rf"\b({MONTHS})\s+(\d{{1,2}}),?\s+(\d{{4}})\b")

# Required fields for each listing
REQUIRED_FIELDS = [
    "id",
    "company_name",
    "title",
    "url",
    "locations",
    "season",
    "category",
    "opportunity_type",
    "target_year",
    "sponsorship",
    "active",
    "is_visible",
    "date_posted",
    "date_updated",
    "source"
]

# Valid categories (informational metadata only — everything lives in one table)
VALID_CATEGORIES = ["Internship", "Program", "Research", "Scholarship", "Fellowship", "Other"]


def get_listings_from_json():
    """Load listings from the JSON file."""
    if not os.path.exists(LISTINGS_FILE):
        return []
    with open(LISTINGS_FILE, "r") as f:
        return json.load(f)


def save_listings_to_json(listings):
    """Save listings to the JSON file."""
    with open(LISTINGS_FILE, "w") as f:
        json.dump(listings, f, indent=2)


def check_schema(listings):
    """Validate that all listings have required fields."""
    for listing in listings:
        for field in REQUIRED_FIELDS:
            if field not in listing:
                raise ValueError(f"Listing {listing.get('id', 'unknown')} missing field: {field}")
    return True


def parse_date(month, day, year):
    """Parse a written-out date like ("Jan", "15", "2027") into a datetime, or None."""
    m = month.replace(".", "")
    if m == "Sept":
        m = "Sep"
    for fmt in ("%B %d %Y", "%b %d %Y"):
        try:
            return datetime.strptime(f"{m} {day} {year}", fmt).replace(tzinfo=PST)
        except ValueError:
            continue
    return None


def find_dates(text):
    """Every parseable date mentioned in text."""
    found = [parse_date(*m.groups()) for m in DATE_RE.finditer(text)]
    return [d for d in found if d]


def earliest_upcoming(text, today):
    """Earliest date in text that has not passed yet, or None."""
    upcoming = [d for d in find_dates(text) if d.date() >= today.date()]
    return min(upcoming) if upcoming else None


def listing_deadline(listing, today):
    """
    Earliest upcoming deadline for a listing, read from the same text the README
    row shows (title, type, locations) so ordering matches the rendered badge.
    """
    text = " ".join([
        listing.get("title", ""),
        listing.get("opportunity_type", ""),
        " ".join(listing.get("locations", []) or []),
    ])
    return earliest_upcoming(text, today)


def is_closing_soon(listing, today):
    """
    True when the listing's next deadline falls inside the closing-soon window.

    A listing whose applications have not opened yet is never "closing soon" --
    its row text mentions the opening date, which would otherwise be read as a
    deadline and wrongly float the row to the top of its table.
    """
    if is_opens_soon(listing, today):
        return False
    deadline = listing_deadline(listing, today)
    if not deadline:
        return False
    return 0 <= (deadline.date() - today.date()).days <= CLOSING_SOON_DAYS


def opens_on(listing):
    """Datetime a not-yet-open listing starts accepting applications, or None."""
    ts = listing.get("opens_on")
    return datetime.fromtimestamp(ts, tz=PST) if ts else None


def is_opens_soon(listing, today):
    """True when applications for this listing have not opened yet."""
    opens = opens_on(listing)
    return bool(opens and opens.date() > today.date())


def sort_listings(listings, today=None):
    """
    Sort listings for display: active first, then closing-soon rows (soonest
    deadline first), then newest by date posted, then company name.

    Floating closing-soon rows to the top is done here rather than by editing
    README.md so the ordering survives every regeneration.
    """
    today = today or datetime.now(tz=PST)

    def key(listing):
        closing = is_closing_soon(listing, today)
        deadline = listing_deadline(listing, today) if closing else None
        return (
            not listing.get("active", False),                # Active first
            not closing,                                     # Closing soon next
            deadline.date() if closing else date.max,        # Soonest deadline first
            -listing.get("date_posted", 0),                  # Newest first
            listing.get("company_name", "").lower(),
        )

    return sorted(listings, key=key)


def sanitize_table_cell(value):
    """Escape pipe characters and newlines in a markdown table cell value."""
    if not isinstance(value, str):
        value = str(value)
    value = value.replace("|", "\\|")
    value = value.replace("\n", " ")
    return value.strip()


def format_locations(locations):
    """Format location list for display."""
    if not locations:
        return "N/A"
    if len(locations) == 1:
        return sanitize_table_cell(locations[0])
    if len(locations) <= 3:
        return ", ".join(sanitize_table_cell(loc) for loc in locations)
    # For many locations, use expandable details
    joined = ", ".join(sanitize_table_cell(loc) for loc in locations)
    return f"<details><summary>{len(locations)} locations</summary>{joined}</details>"


def get_sponsorship_badge(sponsorship):
    """Return emoji badge for sponsorship status."""
    badges = {
        "Does Not Offer Sponsorship": " :no_entry_sign:",
        "U.S. Citizenship Required": " :us:",
        "U.S. Work Authorization Required": " :no_entry_sign:",
    }
    return badges.get(sponsorship, "")


def get_status_badge(active):
    """Return emoji badge for active status."""
    return "" if active else " :lock:"


def format_link(url):
    """Format the application link as a blue button."""
    # Blue "Apply" button using shields.io
    button_url = "https://img.shields.io/badge/Apply-blue?style=for-the-badge"
    return f'<a href="{url}"><img src="{button_url}" alt="Apply"></a>'


def format_date(timestamp):
    """Format Unix timestamp as readable date."""
    dt = datetime.fromtimestamp(timestamp, tz=PST)
    return dt.strftime("%b %d, %Y")


def embed_table(filepath, table, start_marker, end_marker):
    """Embed the generated table between markers in a file."""
    with open(filepath, "r") as f:
        content = f.read()

    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)

    if start_idx == -1 or end_idx == -1:
        raise ValueError(f"Could not find markers in {filepath}")

    new_content = (
        content[:start_idx + len(start_marker)]
        + "\n"
        + table
        + "\n"
        + content[end_idx:]
    )

    with open(filepath, "w") as f:
        f.write(new_content)


def set_output(name, value):
    """Set a GitHub Actions output variable."""
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            # Handle multiline values
            if "\n" in str(value):
                import uuid
                delimiter = uuid.uuid4().hex
                f.write(f"{name}<<{delimiter}\n{value}\n{delimiter}\n")
            else:
                f.write(f"{name}={value}\n")
    else:
        print(f"::set-output name={name}::{value}")


def fail(message):
    """Set error output and exit."""
    set_output("error_message", message)
    print(f"Error: {message}")
    exit(1)


def get_current_timestamp():
    """Get current Unix timestamp."""
    return int(datetime.now(tz=PST).timestamp())


def generate_uuid():
    """Generate a new UUID for a listing."""
    import uuid
    return str(uuid.uuid4())


def clean_url(url):
    """Clean and normalize a URL."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    # Remove common tracking parameters
    tracking_params = ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"]
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    cleaned_params = {k: v for k, v in params.items() if k not in tracking_params}
    cleaned_query = urlencode(cleaned_params, doseq=True)
    cleaned_url = urlunparse(parsed._replace(query=cleaned_query))
    return cleaned_url
