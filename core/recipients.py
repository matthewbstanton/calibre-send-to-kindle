"""Pick the Kindle address to send to from Calibre's email accounts.

``accounts`` throughout is Calibre's email ``accounts`` preference: a dict
mapping an address to ``[formats, auto_send, is_default]``.
"""

#: Domains of Amazon's Send-to-Kindle email service, as recognised by Calibre.
KINDLE_DOMAINS = ('kindle.com', 'free.kindle.com', 'kindle.cn', 'free.kindle.cn')


def _addresses(entry):
    """Split a Calibre account key, which may hold comma-separated addresses."""
    ans = []
    for part in (entry or '').split(','):
        part = part.strip()
        if '<' in part and part.endswith('>'):
            part = part[part.rindex('<') + 1:-1].strip()
        if part:
            ans.append(part.lower())
    return ans


def is_kindle_address(entry):
    """True if any address in ``entry`` is a Send-to-Kindle address."""
    for addr in _addresses(entry):
        domain = addr.rpartition('@')[2]
        if domain in KINDLE_DOMAINS:
            return True
    return False


def _is_default(accounts, address):
    value = accounts.get(address)
    try:
        return bool(value[2])
    except (TypeError, IndexError):
        return False


def kindle_accounts(accounts):
    """Return the Kindle addresses in ``accounts``, Calibre's default first."""
    found = [a for a in (accounts or {}) if is_kindle_address(a)]
    found.sort(key=lambda a: not _is_default(accounts, a))
    return found


def resolve_recipient(configured, accounts):
    """Return the address to send to, or None if there is none.

    A ``configured`` address is used only if it is still one of Calibre's
    accounts. With nothing configured, the first Kindle address is used,
    preferring the one marked as Calibre's default.
    """
    accounts = accounts or {}
    configured = (configured or '').strip()
    if configured:
        return configured if configured in accounts else None
    found = kindle_accounts(accounts)
    return found[0] if found else None
