import requests
from CallAPI.config import BASE_URL, API_KEY, DEFAULT_CHAT_MODEL, CHAT_KWARGS

import requests
from requests.exceptions import Timeout, ConnectionError, HTTPError
import time

def call_chat_api(prompt=None, chat_model=None, extra_kwargs=None, max_retries=3, retry_delay=0.2, messages=None, max_tokens=4096):
    """
    Call chat API to send request and get response
    
    Args:
        prompt (str, optional): Single user message content
        chat_model (str, optional): Chat model to use, defaults to DEFAULT_CHAT_MODEL in config
        extra_kwargs (dict, optional): Additional request parameters
        max_retries (int, optional): Maximum retry attempts, defaults to 3
        retry_delay (float, optional): Initial retry delay time (seconds), defaults to 0.2
        messages (list, optional): Complete message list, takes priority if provided
        max_tokens (int, optional): Maximum token limit for generated text
    
    Returns:
        str: Text content returned by API
    """
    url = f"{BASE_URL}/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    # Build message list
    if messages is not None:
        # If messages is directly provided, use it
        message_list = messages
    elif prompt is not None:
        # If prompt is provided, build traditional format messages
        message_list = [{"role": "user", "content": prompt}]
    else:
        raise ValueError("Must provide either prompt or messages parameter")
    # print("message_list:", message_list)
    payload = {
        "model": chat_model or DEFAULT_CHAT_MODEL,
        "messages": message_list,
        "stream": False,
        **CHAT_KWARGS
    }
    
    # If max_tokens is set, add to request (will override default value in CHAT_KWARGS)
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if extra_kwargs:
        # Update extra_kwargs first, but don't override messages we've already set
        extra_kwargs_copy = extra_kwargs.copy()
        if "messages" in extra_kwargs_copy:
            extra_kwargs_copy.pop("messages")  # Remove messages to avoid override
        payload.update(extra_kwargs_copy)
        
    retries = 0
    while retries <= max_retries:
        try:
            # Set timeout parameters (connection timeout and read timeout)
            resp = requests.post(url, headers=headers, json=payload, timeout=(5, 10))
            resp.raise_for_status()  # Check HTTP status code
            return resp.json()["choices"][0]["message"]["content"].strip()
            
        except Timeout as e:
            print(f"Request timeout: {e}")
        except ConnectionError as e:
            print(f"Connection failed: {e}")
        except HTTPError as e:
            # Some HTTP errors (like 400, 401, 403) should not be retried
            if 400 <= e.response.status_code < 500:
                print(f"Client error ({e.response.status_code}), no more retries")
                raise
            print(f"Server error ({e.response.status_code}): {e}")
        except Exception as e:
            print(f"Unknown error: {e}")
        
        # Retry logic
        retries += 1
        if retries <= max_retries:
            wait_time = retry_delay * (2 ** (retries - 1))  # Exponential backoff strategy
            print(f"Will retry in {wait_time} seconds ({retries}/{max_retries})")
            time.sleep(wait_time)
        else:
            print("All retries failed, returning None")
            return None  # Return None if all retries fail
