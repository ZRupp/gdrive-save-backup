import json

def save_to_json(dict_to_save: dict, destination: str) -> None:
    """Simple method for saving dictionary in json format.

    TODO: - Error Handling
    """

    try:
        with open(destination, "w", encoding="utf-8") as f:
            json.dump(dict_to_save, f, ensure_ascii=False)
    except Exception as e:
        print(e.message)


def load_from_json(location: str) -> dict:
    """Simple method to load a dict from json.

    TODO:   - Either in this method or another, ensure that folders exist and remove
              them if not.
            - Error Handling
    """
    try:
        with open(location, "r", encoding="utf-8") as f:
            loaded_dict = json.load(f)
    except json.JSONDecodeError:
        print(f"Error reading `{location}`. Returning blank dictionary.")
        loaded_dict = {}

    return loaded_dict