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

import importlib.metadata
from pathlib import Path

import typer

import elevation

from . import spatial

CONTEXT_SETTINGS = {"auto_envvar_prefix": "EIO"}

app = typer.Typer(
    context_settings=CONTEXT_SETTINGS,
    add_completion=False,
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    if value:
        version = importlib.metadata.version("elevation")
        typer.echo(f"eio, version {version}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show the version and exit.",
    ),
    product: str = typer.Option(
        elevation.DEFAULT_PRODUCT,
        "--product",
        metavar="[" + "|".join(elevation.PRODUCTS) + "]",
        help="DEM product choice.",
    ),
    cache_dir: Path = typer.Option(
        elevation.CACHE_DIR,
        "--cache_dir",
        file_okay=False,
        # typer annotates path_type as "type[str] | type[bytes] | None" while
        # TyperPath accepts any type at runtime.
        path_type=Path,  # type: ignore[arg-type]
        help="Root of the DEM cache folder.",
    ),
    make_options: str = typer.Option(
        "",
        "--make_options",
        help="Options passed through to every GNU make invocation.",
    ),
) -> None:
    if product not in elevation.PRODUCTS:
        raise typer.BadParameter(
            f"{product!r} is not one of "
            f"{', '.join(repr(item) for item in elevation.PRODUCTS)}.",
            param_hint="--product",
        )
    ctx.obj = {
        "cache_dir": cache_dir,
        "product": product,
        "make_options": make_options,
    }


@app.command(short_help="Audit the system for common issues.")
def selfcheck() -> None:
    typer.echo(elevation.selfcheck())


@app.command(short_help="Show info about the product cache.")
def info(ctx: typer.Context) -> None:
    elevation.info(**ctx.obj)


@app.command(short_help="Seed the DEM to given bounds.")
def seed(
    ctx: typer.Context,
    bounds: tuple[float, float, float, float] | None = typer.Option(
        None,
        "--bounds",
        help="Output bounds: left bottom right top.",
    ),
) -> None:
    elevation.seed(**ctx.obj, bounds=bounds)


@app.command(short_help="Clip the DEM to given bounds.")
def clip(
    ctx: typer.Context,
    output: Path = typer.Option(
        elevation.DEFAULT_OUTPUT,
        "-o",
        "--output",
        dir_okay=False,
        path_type=Path,  # type: ignore[arg-type]
        help="Path to output file. Existing files will be overwritten.",
    ),
    bounds: tuple[float, float, float, float] | None = typer.Option(
        None,
        "--bounds",
        help="Output bounds in 'left bottom right top' order.",
    ),
    margin: str = typer.Option(
        elevation.MARGIN,
        "-m",
        "--margin",
        help="Decimal degree margin added to the bounds. Use '%' for percent margin.",
    ),
    reference: Path | None = typer.Option(
        None,
        "-r",
        "--reference",
        exists=True,
        path_type=Path,  # type: ignore[arg-type]
        help="Use the extent of a reference GDAL/OGR data source as output bounds.",
    ),
) -> None:
    if bounds is None and reference is None:
        raise typer.BadParameter(
            message="One of --bounds or --reference must be supplied.",
            param_hint="--bounds",
        )
    if bounds is None:
        assert reference is not None
        bounds = spatial.import_bounds(reference)
    elevation.clip(bounds, output=output, margin=margin, **ctx.obj)


@app.command(short_help="Clean up the product cache from temporary files.")
def clean(ctx: typer.Context) -> None:
    elevation.clean(**ctx.obj)


@app.command(short_help="Remove the product cache entirely.")
def distclean(ctx: typer.Context) -> None:
    elevation.distclean(**ctx.obj)


if __name__ == "__main__":
    app()
