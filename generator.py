import json
import os
import hashlib
from functools import wraps
from claudette import Chat
import traceback


def disk_cache(cache_dir=".llm_cache"):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create a unique key based on function arguments
            key = hashlib.md5(
                json.dumps((args, kwargs), sort_keys=True).encode()
            ).hexdigest()
            cache_file = os.path.join(cache_dir, f"{func.__name__}_{key}.json")

            force_refresh = kwargs.get("force_refresh", False)

            if os.path.exists(cache_file) and not force_refresh:
                with open(cache_file, "r") as f:
                    return json.load(f)

            result = func(*args, **kwargs)
            os.makedirs(cache_dir, exist_ok=True)
            with open(cache_file, "w") as f:
                json.dump(result, f)

            return result

        return wrapper

    return decorator


@disk_cache()
def generate_content(
    messages,
    model="claude-3-5-sonnet-20240620",
    prefill='<!DOCTYPE html>\n<html lang="en">',
    system_prompt="""You are an expert web developer, you are tasked with producing a single html files.  All of your code should be inline in the html file, but you can use CDNs to import packages if needed.""",
    force_refresh=False,
):
    try:
        chat = Chat(model, sp=system_prompt)
        r = chat(messages, prefill=prefill)

        return parse(r)

    except Exception as e:
        return f"<title>error</title><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>"


def parse(r):
    return r.content[0].text
