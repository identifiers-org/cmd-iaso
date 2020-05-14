import click


class ValidateMutexCommand(click.Command):
    def make_context(self, *args, **kwargs):
        ctx = super(ValidateMutexCommand, self).make_context(*args, **kwargs)

        for param in self.params:
            if isinstance(param, MutexOption):
                ValidateMutexCommand.validate_mutex(
                    ctx.params, param.name, param.not_required_if
                )

        return ctx

    @staticmethod
    def validate_mutex(params, cmd_name, not_required_if):
        exlusivity = []

        for mutex_opt in not_required_if:
            mutex_opt_name, mutext_opt_val = mutex_opt.split("=")

            if "=" in mutex_opt:
                exlusivity.append(f"--{mutex_opt_name} {mutext_opt_val}")
            else:
                exlusivity.append(f"--{mutex_opt_name}")

            if (mutex_opt_name not in params or params[mutex_opt_name] is None) or (
                ("=" in mutex_opt) and (params[mutex_opt_name] != mutext_opt_val)
            ):
                return True

        if cmd_name in params and params[cmd_name] is not None:
            raise click.UsageError(
                "illegal usage: '{name}' is mutually exclusive with '{exclusivity}'.".format(
                    name=cmd_name, exclusivity=" ".join(exlusivity)
                )
            )

        return False


class MutexOption(click.Option):
    def __init__(self, *args, **kwargs):
        self.not_required_if = kwargs.pop("not_required_if")

        assert self.not_required_if is not None, "'not_required_if' parameter required"

        kwargs["help"] = (
            kwargs.get("help", "")
            + "Option is mutually exclusive with "
            + ", ".join(self.not_required_if)
            + "."
        ).strip()

        super(MutexOption, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if not ValidateMutexCommand.validate_mutex(
            dict(ctx.params, **opts), self.name, self.not_required_if
        ):
            self.prompt = None
            self.default = None

        return super(MutexOption, self).handle_parse_result(ctx, opts, args)
