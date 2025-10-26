from app.services.validation_service import get_related_misconceptions

if __name__ == "__main__":
    topic = "Newton's Laws"
    results = get_related_misconceptions(topic)
    print(f"Top misconceptions for '{topic}':")
    for item in results:
        print(
            "- {subject} / {concept}: {misconception} -> {correction}".format(
                subject=item.get("subject"),
                concept=item.get("concept"),
                misconception=item.get("misconception_text"),
                correction=item.get("correction"),
            )
        )
