import ipaddress

import click


class ChromeChoice(click.Choice):
    name = "chrome-choice"

    def __init__(self, case_sensitive=True):
        self.choices = ["'launch'", "IPv4:PORT", "[IPv6]:PORT"]
        self.case_sensitive = case_sensitive

    def convert(self, value, param, ctx):
        normed_value = value
        normed_choices = {"launch": "launch"}

        if ctx is not None and ctx.token_normalize_func is not None:
            normed_value = ctx.token_normalize_func(value)
            normed_choices = {
                ctx.token_normalize_func(normed_choice): original
                for normed_choice, original in normed_choices.items()
            }

        if not self.case_sensitive:
            normed_value = normed_value.casefold()
            normed_choices = {
                normed_choice.casefold(): original
                for normed_choice, original in normed_choices.items()
            }

        if normed_value in normed_choices:
            return normed_choices[normed_value]

        ip_address, _, port = normed_value.rpartition(":")

        try:
            ip_address = (
                ipaddress.ip_address(ip_address.strip("[]"))
                if ip_address != "localhost"
                else "localhost"
            )
            port = int(port)
            assert port > 0
        except:
            self.fail(
                f"invalid choice: {value}. (choose from {', '.join(self.choices)})",
                param,
                ctx,
            )

        return f"{ip_address}:{port}"
