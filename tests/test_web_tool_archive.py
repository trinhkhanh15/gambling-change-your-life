from dotenv import load_dotenv
load_dotenv()

from service.tools.web_tool import WebTool
from infra.storage.archive import JsonArchive
from domain.schema.event import Event

def main():
    web_tool = WebTool()
    archive = JsonArchive(base_dir="data")

    events = web_tool.search_and_decompose(
        "Hoyoverse earning 2026", max_results=2
    )
    print(f"Fetched {len(events)} events")

    for event in events:
        archive.append_jsonl("events", event)
        print(f"  saved: {event.id} - {event.title}")

    loaded = archive.load_jsonl("events", Event)
    print(f"Loaded back {len(loaded)} events from storage")

if __name__ == "__main__":
    main()