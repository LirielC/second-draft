"""Create a separate fictional archive for portfolio demonstrations."""
import argparse
from second_draft.archive import Archive

def main():
    parser = argparse.ArgumentParser(description="Seed fictional Second Draft projects")
    parser.add_argument("--database", default="data/demo.db")
    args = parser.parse_args()
    archive = Archive(args.database)
    if archive.search():
        parser.error("Demo archive must be empty; choose a new database path")
    archive.create("Pantry Atlas", "A recipe finder based on pantry ingredients.",
        "Manual recipe entry became too time-consuming.",
        ["Start with a small curated dataset."], ["Ingredient search", "Recipe card layout"], ["python", "food", "search"])
    archive.create("Weekend Compass", "A planner for short weekend adventures.",
        "Live integrations made the scope too large.",
        ["A useful prototype can work with manual inputs."], ["Preference filters", "Itinerary checklist"], ["planning", "travel"])
    archive.create("Tiny Habits", "A daily habit tracker with progress summaries.",
        "Too many dashboards distracted from the main workflow.",
        ["Choose one primary view."], ["Check-in form", "Weekly progress summary"], ["tracking", "python"])
    print(f"Created 3 fictional projects in {args.database}")

if __name__ == "__main__":
    main()
