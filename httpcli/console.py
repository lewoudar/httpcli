from rich.console import Console
from rich.style import Style
from rich.theme import Theme

custom_theme = Theme({
    'error': Style(color='red'),
    'info': Style(color='blue')
})

console = Console(theme=custom_theme)
