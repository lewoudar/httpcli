import difflib

import asyncclick as click


class DYMMixin:
    """
    Mixin class for click MultiCommand inherited classes to provide git-like *did-you-mean* functionality when
    a certain command is not registered.
    """

    def __init__(self, *args, **kwargs):
        self.max_suggestions = kwargs.pop('max_suggestions', 3)
        self.cutoff = kwargs.pop('cutoff', 0.5)
        super(DYMMixin, self).__init__(*args, **kwargs)

    async def resolve_command(self, ctx, args):
        """
        Overrides asyncclick resolve_command method and appends *Did you mean ...* suggestions
        to the raised exception message.
        """
        try:
            return await super(DYMMixin, self).resolve_command(ctx, args)
        except click.UsageError as error:
            error_message = str(error)
            original_cmd_name = click.utils.make_str(args[0])
            matches = difflib.get_close_matches(
                original_cmd_name, self.list_commands(ctx), self.max_suggestions, self.cutoff
            )

            if matches:
                error_message += f'\n\nDid you mean one of these?\n'
                for command_name in matches:
                    error_message += f'    • {command_name}\n'

            raise click.UsageError(error_message[:-1], error.ctx)


class DYMGroup(DYMMixin, click.Group):
    """
    click Group to provide git-like *did-you-mean* functionality when a certain
    command is not found in the group.
    """
