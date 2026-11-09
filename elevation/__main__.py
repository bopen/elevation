#
# Copyright (c) 2016-2026 B-Open Solutions srl - https://bopen.eu
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pathlib import Path
from typing import Any

import click

import elevation

from . import spatial

CONTEXT_SETTINGS = {"auto_envvar_prefix": "EIO", "show_default": True}
PRODUCTS_METAVAR = "[" + "|".join(elevation.PRODUCTS) + "]"

# the options shared by seed and clip
bounds_option = click.option(
    "--bounds",
    type=(float, float, float, float),
    help="Output bounds in 'left bottom right top' order.",
    show_envvar=True,
)
margin_option = click.option(
    "-m",
    "--margin",
    default=elevation.MARGIN,
    help="Decimal degree margin added to the bounds. Use '%' for percent margin.",
    show_envvar=True,
)
max_download_tiles_option = click.option(
    "--max_download_tiles",
    default=elevation.MAX_DOWNLOAD_TILES,
    help="Maximum number of tiles to download.",
    show_envvar=True,
)


class OrderedGroup(click.Group):
    """List the commands in the order they are defined, not alphabetically."""

    def list_commands(self, ctx: click.Context) -> list[str]:
        return list(self.commands)


@click.group("eio", cls=OrderedGroup, context_settings=CONTEXT_SETTINGS)
@click.version_option(package_name="elevation", prog_name="eio")
@click.option(
    "--product",
    default=elevation.DEFAULT_PRODUCT,
    metavar=PRODUCTS_METAVAR,
    help="DEM product choice.",
    show_envvar=True,
)
@click.option(
    "--cache_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=elevation.CACHE_DIR,
    help="Root of the DEM cache folder.",
    show_envvar=True,
)
@click.pass_context
def app(ctx: click.Context, product: str, cache_dir: Path) -> None:
    if product in elevation.RETIRED_PRODUCTS:
        raise click.BadParameter(
            elevation.RETIRED_PRODUCTS[product], param_hint="--product"
        )
    if product not in elevation.PRODUCTS:
        raise click.BadParameter(
            f"{product!r} is not one of "
            f"{', '.join(repr(item) for item in elevation.PRODUCTS)}.",
            param_hint="--product",
        )
    ctx.obj = {
        "cache_dir": cache_dir,
        "product": product,
    }


@app.command()
@click.option(
    "--verbose",
    is_flag=True,
    help="Report each tool as it is tested.",
    show_envvar=True,
)
def selfcheck(verbose: bool) -> None:
    """Audit the system for common issues."""
    click.echo(elevation.selfcheck(verbose=verbose))


@app.command()
@click.pass_obj
def info(obj: dict[str, Any]) -> None:
    """Show info about the product cache."""
    click.echo(elevation.info(**obj))


@app.command()
@click.argument("dataset", required=False)
def dataset(dataset: str | None) -> None:
    """Show the STAC metadata of the datasets.

    \b
    Arguments:
      DATASET  Dataset choice, one of the --product values, all of them if not given.
    """  # noqa: D301 click needs the backspace in "\b" to keep the lines
    if dataset is not None and dataset not in elevation.PRODUCTS:
        raise click.BadParameter(
            f"{dataset!r} is not one of "
            f"{', '.join(repr(item) for item in elevation.PRODUCTS)}.",
            param_hint="dataset",
        )
    click.echo(elevation.dataset(dataset))


@app.command()
@bounds_option
@margin_option
@max_download_tiles_option
@click.pass_obj
def seed(
    obj: dict[str, Any],
    bounds: tuple[float, float, float, float] | None,
    margin: str,
    max_download_tiles: int,
) -> None:
    """Seed the DEM to given bounds."""
    if bounds is None:
        raise click.BadParameter(
            message="--bounds must be supplied.",
            param_hint="--bounds",
        )
    elevation.seed(
        **obj,
        bounds=bounds,
        margin=margin,
        max_download_tiles=max_download_tiles,
    )


@app.command()
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    default=elevation.DEFAULT_OUTPUT,
    help="Path to output file. Existing files will be overwritten.",
    show_envvar=True,
)
@bounds_option
@margin_option
@click.option(
    "-r",
    "--reference",
    type=click.Path(exists=True, path_type=Path),
    help="Use the extent of a reference GDAL/OGR data source as output bounds.",
    show_envvar=True,
)
@click.option(
    "--gdal-options",
    help=(
        "GDAL creation options of the output file, e.g. '-co COMPRESS=LZW'. "
        "The default is the options of the product cached tiles: DEFLATE "
        "compression with the predictor that suits the product."
    ),
    show_default=False,
    show_envvar=True,
)
@max_download_tiles_option
@click.pass_obj
def clip(
    obj: dict[str, Any],
    output: Path,
    bounds: tuple[float, float, float, float] | None,
    margin: str,
    reference: Path | None,
    gdal_options: str | None,
    max_download_tiles: int,
) -> None:
    """Clip the DEM to given bounds."""
    if bounds is None and reference is None:
        raise click.BadParameter(
            message="One of --bounds or --reference must be supplied.",
            param_hint="--bounds",
        )
    if bounds is None:
        assert reference is not None
        bounds = spatial.import_bounds(reference)
    elevation.clip(
        bounds,
        output=output,
        margin=margin,
        gdal_options=gdal_options,
        max_download_tiles=max_download_tiles,
        **obj,
    )


@app.command()
@click.pass_obj
def clean(obj: dict[str, Any]) -> None:
    """Clean up the product cache from temporary files."""
    elevation.clean(**obj)


@app.command()
@click.pass_obj
def distclean(obj: dict[str, Any]) -> None:
    """Remove the product cache entirely."""
    elevation.distclean(**obj)


if __name__ == "__main__":
    app()
