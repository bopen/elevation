# -*- coding: utf-8 -*-
#
# Copyright (c) 2016-2021 B-Open Solutions srl - http://bopen.eu
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import functools

import click

import elevation

from . import spatial, util

# disable overzealous warning
click.disable_unicode_literals_warning = True


CONTEXT_SETTINGS = dict(auto_envvar_prefix="EIO")


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option()
@click.option(
    "--product",
    type=click.Choice(elevation.PRODUCTS),
    default=elevation.DEFAULT_PRODUCT,
    show_default=True,
    help="DEM product choice.",
)
@click.option(
    "--cache_dir",
    type=click.Path(resolve_path=True, file_okay=False),
    default=elevation.CACHE_DIR,
    show_default=True,
    help="Root of the DEM cache folder.",
)
def eio(**kwargs):
    pass


@eio.command(short_help="Audit the system for common issues.")
def selfcheck():
    print(util.selfcheck(tools=elevation.TOOLS))


def click_merge_parent_params(wrapped):
    @click.pass_context
    @functools.wraps(wrapped)
    def wrapper(ctx, **kwargs):
        if ctx.parent and ctx.parent.params:
            kwargs.update(ctx.parent.params)
        return wrapped(**kwargs)

    return wrapper


@eio.command(short_help="Show info about the product cache.")
@click_merge_parent_params
def info(**kwargs):
    elevation.info(**kwargs)


@eio.command(short_help="Seed the DEM to given bounds.")
@click.option(
    "--bounds", nargs=4, type=float, help="Output bounds: left bottom right top."
)
@click_merge_parent_params
def seed(**kwargs):
    elevation.seed(**kwargs)


@eio.command(short_help="Clip the DEM to given bounds.")
@click.option(
    "-o",
    "--output",
    type=click.Path(resolve_path=True, dir_okay=False),
    default=elevation.DEFAULT_OUTPUT,
    show_default=True,
    help="Path to output file. Existing files will be overwritten.",
)
@click.option(
    "--bounds",
    type=float,
    nargs=4,
    help="Output bounds in 'left bottom right top' order.",
)
@click.option(
    "-m",
    "--margin",
    default=elevation.MARGIN,
    show_default=True,
    help="Decimal degree margin added to the bounds. Use '%' for percent margin.",
)
@click.option(
    "-r",
    "--reference",
    help="Use the extent of a reference GDAL/OGR data source as output bounds.",
)
@click_merge_parent_params
def clip(bounds, reference, **kwargs):
    if not bounds and not reference:
        raise click.BadOptionUsage("One of --bounds or --reference must be supplied.")
    if not bounds:
        bounds = spatial.import_bounds(reference)
    elevation.clip(bounds, **kwargs)


@eio.command(short_help="Clean up the product cache from temporary files.")
@click_merge_parent_params
def clean(**kwargs):
    elevation.clean(**kwargs)


@eio.command(short_help="Remove the product cache entirely.")
@click_merge_parent_params
def distclean(**kwargs):
    elevation.distclean(**kwargs)
