import mailbox
import mimetypes
from pathlib import Path
from typing import IO, Tuple, Set, List

import anyio
import asyncclick as click
import httpx
from pydantic import BaseModel, AnyHttpUrl, ValidationError
from rich.progress import Progress, TaskID

from httpcli.configuration import Configuration
from httpcli.console import console
from httpcli.helpers import build_base_httpx_arguments
from httpcli.parameters import URL


def get_filename_from_content_disposition(response: httpx.Response) -> str:
    disposition = response.headers.get('content-disposition')

    if disposition is None:
        return ''

    message = mailbox.Message(f'content-disposition: {disposition}')
    return message.get_filename(failobj='')


def get_filename_from_url(response: httpx.Response) -> str:
    url = response.request.url
    filename = url.path.split('/')[-1]

    if Path(filename).suffix:
        return filename

    content_type = response.headers.get('content-type')
    if content_type is None:
        return filename

    extension = mimetypes.guess_extension(content_type)
    if extension is None:
        return filename

    return f'{filename.rstrip(".")}{extension}'


def get_filename(response: httpx.Response) -> str:
    filename = get_filename_from_content_disposition(response)
    if filename:
        return filename

    return get_filename_from_url(response)


class FileModel(BaseModel):
    urls: List[AnyHttpUrl]


def get_urls_from_file(file: IO[str]) -> Set[str]:
    urls = [line.strip() for line in file]

    try:
        FileModel(urls=urls)  # type: ignore
    except ValidationError as e:
        raise click.UsageError(str(e))

    return set(urls)


async def download_file(
        client: httpx.AsyncClient,
        url: str,
        allow_redirects: bool,
        destination: Path,
        progress: Progress,
        task_id: TaskID
) -> None:
    response = await client.get(url, allow_redirects=allow_redirects)
    filename = get_filename(response)
    if response.status_code >= 300:  # we take in account cases where users deny redirects
        progress.console.print(f':cross_mark: {url} ({filename})')
        progress.update(task_id, advance=1)
    else:
        path = destination / filename
        path.write_bytes(response.content)
        progress.console.print(f':white_heavy_check_mark: {url} ({filename})')
        progress.update(task_id, advance=1)


@click.command()
@click.option(
    '-d', '--destination',
    help='The directory where downloaded files will be saved. If not provided, default to the current directory.',
    type=click.Path(exists=True, file_okay=False)
)
@click.option(
    '-f', '--file',
    help='File containing one url per line. Each url corresponds to a file to download.',
    type=click.File()
)
@click.argument('url', type=URL, nargs=-1)
@click.pass_obj
# well, technically url is not a str but a pydantic.AnyHttpUrl object inheriting from str
# but it does not seem to bother httpx, so we can use the convenient str for signature
async def download(config: Configuration, destination: str, file: IO[str], url: Tuple[str, ...]):
    """
    Process download of urls given as arguments.

    URL is an url targeting a file to download. It can be passed multiple times.

    You can combine url arguments with --file option.
    """
    urls = set(url)
    if file:
        other_urls = get_urls_from_file(file)
        urls = urls.union(other_urls)

    destination = Path(destination) if destination else Path.cwd()
    arguments = build_base_httpx_arguments(config)
    allow_redirects = arguments.pop('allow_redirects')

    with Progress(console=console) as progress:
        task_id = progress.add_task('Downloading', total=len(urls))
        async with httpx.AsyncClient(**arguments) as client:
            async with anyio.create_task_group() as tg:
                for url in urls:
                    tg.start_soon(download_file, client, url, allow_redirects, destination, progress, task_id)

    console.print('[info]Downloads completed! :glowing_star:')
