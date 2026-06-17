def clean_text(text):
    return text.strip()


def extract_text(result_json):
    return result_json.get("text", "")