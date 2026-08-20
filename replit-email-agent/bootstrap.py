"""Wire this repl to a CarlyEmail inbox at boot.

The reason this template exists. Every other quickstart stalls on the same
step: inbound mail needs a public HTTPS URL, and getting one means ngrok, or a
deploy, or a tunnel that dies when you close the laptop. Replit hands you one
for free — so the setup that is normally four manual steps is none.

On boot this figures out its own public URL, makes sure there is an inbox, and
points a webhook at itself. The signing secret is returned once at creation and
kept in memory, which is why the webhook is recreated on every boot rather than
reused.
"""

from __future__ import annotations

import os

import httpx

# Stamped on every webhook we create so we can recognize and clean up our own
# from a previous boot. Replit hands out a new dev URL per session, so without
# this the account slowly fills with webhooks pointing at dead hostnames.
CLIENT_ID = "replit-email-agent"

BASE_URL = os.environ.get("CARLYEMAIL_BASE_URL", "https://api.carlyemail.com").rstrip("/")


class SetupError(RuntimeError):
    """Something the operator has to fix. Raised at boot, never mid-request."""


def public_base_url() -> str:
    """The URL the outside world reaches this repl on.

    `REPLIT_DEV_DOMAIN` only exists in the workspace, and `REPLIT_DOMAINS` is
    set in both the workspace and a deployment — so deployments are checked
    first and the dev domain is the fallback. `PUBLIC_URL` overrides both, for
    a custom domain or for running this outside Replit.
    """
    override = os.environ.get("PUBLIC_URL")
    if override:
        return override.rstrip("/")

    domains = os.environ.get("REPLIT_DOMAINS", "")
    for domain in domains.split(","):
        if domain.strip():
            return f"https://{domain.strip()}"

    dev_domain = os.environ.get("REPLIT_DEV_DOMAIN")
    if dev_domain:
        return f"https://{dev_domain}"

    raise SetupError(
        "Cannot work out this repl's public URL. Set PUBLIC_URL to the address "
        "this server is reachable at."
    )


def _client(api_key: str) -> httpx.Client:
    return httpx.Client(
        base_url=BASE_URL,
        headers={"authorization": f"Bearer {api_key}"},
        timeout=30.0,
    )


def _raise_for_status(response: httpx.Response, doing: str) -> None:
    if response.is_success:
        return
    if response.status_code in (401, 403):
        raise SetupError(
            f"CarlyEmail rejected the API key while {doing}. Check the "
            "CARLYEMAIL_API_KEY secret."
        )
    raise SetupError(
        f"CarlyEmail returned {response.status_code} while {doing}: {response.text[:300]}"
    )


def ensure_inbox(client: httpx.Client) -> str:
    """The inbox named in the environment, the first one on the account, or a new one."""
    wanted = os.environ.get("CARLYEMAIL_INBOX")
    if wanted:
        return wanted

    response = client.get("/v0/inboxes", params={"limit": 1})
    _raise_for_status(response, "listing inboxes")
    inboxes = response.json().get("inboxes") or []
    if inboxes:
        return inboxes[0]["inbox_id"]

    response = client.post("/v0/inboxes", json={"client_id": CLIENT_ID})
    _raise_for_status(response, "creating an inbox")
    return response.json()["inbox_id"]


def _delete_our_webhooks(client: httpx.Client) -> int:
    """Remove webhooks this template created on a previous boot.

    Matched on client_id rather than URL: the previous boot's URL is usually a
    dev domain that no longer exists, so a URL match would leave it behind.
    """
    response = client.get("/v0/webhooks", params={"limit": 100})
    _raise_for_status(response, "listing webhooks")

    removed = 0
    for webhook in response.json().get("webhooks") or []:
        if webhook.get("client_id") != CLIENT_ID:
            continue
        client.delete(f"/v0/webhooks/{webhook['webhook_id']}")
        removed += 1
    return removed


def setup() -> dict[str, str]:
    """Resolve everything this server needs. Called once, before it serves."""
    api_key = os.environ.get("CARLYEMAIL_API_KEY")
    if not api_key:
        raise SetupError(
            "CARLYEMAIL_API_KEY is not set. Add it under Secrets in the sidebar. "
            "Get a key with: npx carlyemail signup --human-email you@example.com "
            "--username assistant"
        )
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SetupError("ANTHROPIC_API_KEY is not set. Add it under Secrets in the sidebar.")

    url = f"{public_base_url()}/webhook"

    with _client(api_key) as client:
        inbox_id = ensure_inbox(client)
        stale = _delete_our_webhooks(client)

        response = client.post(
            "/v0/webhooks",
            json={
                "url": url,
                # Only inbound mail. Subscribing to everything would mean the
                # agent's own sends came back as events it had to filter.
                "event_types": ["message.received"],
                "inbox_ids": [inbox_id],
                "client_id": CLIENT_ID,
            },
        )
        _raise_for_status(response, "creating the webhook")
        webhook = response.json()

    secret = webhook.get("secret")
    if not secret:
        # Without the secret there is no way to tell a real delivery from
        # anyone who found the URL, so this is fatal rather than a warning.
        raise SetupError(
            "CarlyEmail created the webhook but returned no signing secret. The "
            "secret is shown only at creation; delete the webhook and restart."
        )

    return {
        "inbox_id": inbox_id,
        "webhook_id": webhook["webhook_id"],
        "webhook_url": url,
        "webhook_secret": secret,
        "stale_webhooks_removed": str(stale),
    }
