from typing import NoReturn, List, Tuple
import os
from functools import partial
import traceback
from time import sleep

import requests


def main() -> NoReturn:
    try:
        pings_str = os.getenv("PINGS")
        freq_str = os.getenv("FREQ")
        dest_email = os.getenv("DEST_EMAIL")
        from_email = os.getenv("FROM_EMAIL")
        mailgun_domain = os.getenv("MAILGUN_DOMAIN")
        mailgun_api_key = os.getenv("MAILGUN_API_KEY")
        assert pings_str is not None
        assert freq_str is not None
        assert dest_email is not None
        assert dest_email is not None
        assert mailgun_domain is not None
        assert mailgun_api_key is not None
        pings = parse_pings(pings_str)
        freq = int(freq_str)
        send_email_configured = partial(send_email,
                                        dest_email=dest_email, from_email_name="Pings", from_email=from_email,
                                        mailgun_domain=mailgun_domain, mailgun_api_key=mailgun_api_key)
    except:
        traceback.print_exc()
        print()
        print("""
Usage: python3 pings.py
Ensure this env variables:
    PINGS:
        List of endpoints to ping.
        Example: example.com,secured.example.com=401
    FREQ:
        Frequency in minutes.
    DEST_EMAIL
    FROM_EMAIL
    MAILGUN_DOMAIN
    MAINGUN_API_KEY
        """.strip())
        exit(1)

    while True:
        sleep(freq * 60)

        for ping in pings:
            ok, data = ping_endpoint(**ping)
            if not ok:
                print(f"Failed ping from {ping['url']}")
                text = f"""
Failed ping from {ping['url']}.
Expected status code {ping['expected_http_code']}.
Got {data}
                """.strip()
                mailgun_response = send_email_configured(subject=f"Failed ping from {ping['url']}", text=text)
                assert mailgun_response.status_code == 200


def parse_pings(pings_str: str) -> List[dict]:
    result = list()
    for ping_str in pings_str.split(","):
        if "=" in ping_str:
            url, expected_http_code = ping_str.split("=")
            expected_http_code = int(expected_http_code)
        else:
            url = ping_str
            expected_http_code = 200
        if not url.startswith("http"):
            url = "http://" + url
        result.append({"url": url, "expected_http_code": expected_http_code})
    return result


def ping_endpoint(url, expected_http_code: int = 200) -> Tuple[bool, requests.Response]:
    try:
        r = requests.head(url)
        return r.status_code == expected_http_code, r
    except Exception as e:
        return False, e


def send_email(subject: str, text: str, dest_email: str, from_email_name: str, from_email: str, mailgun_domain: str, mailgun_api_key: str) -> requests.Response:
    return requests.post(
        f"https://api.mailgun.net/v3/{mailgun_domain}/messages",
        auth=("api", mailgun_api_key),
        data={"from": f"{from_email_name} <{from_email}>",
              "to": [dest_email],
              "subject": subject,
              "text": text})


if __name__ == "__main__":
    main()
