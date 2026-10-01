DATASOURCE_URL := {datasource_url}
PRODUCT := {product}

# Remote products are read in place: nothing is downloaded, nothing is cached and
# there is no local artefact beyond this Makefile, so clip is the only target
# that touches the dataset.
#
# The connection string may contain double quotes, as in the
# ZARR:"/vsicurl/https://..." form that the Zarr driver requires for a store
# with no reliable directory listing, and may carry a trailing :/array suffix
# when the store exposes more than one array: the outer single quotes below
# keep them intact through the shell, so the string must not contain a single
# quote itself.
SOURCE := '$(DATASOURCE_URL)'

# GDAL configuration options, as a space separated list of KEY=VALUE
# assignments, prefixed to every GDAL command, e.g.
# GDAL_DISABLE_READDIR_ON_OPEN=EMPTY_DIR or GDAL_HTTP_BEARER=a-token. The
# Python API and the eio command line set it from EIO_GDAL_CONFIG.
GDAL_CONFIG ?=

# nothing to prepare: the dataset is read in place by clip
all:
	@echo '$(PRODUCT) is a remote dataset, nothing to prepare'

# The crop is done with gdalwarp rather than gdal_translate -projwin: these stores
# are bottom-up (their Y coordinate increases with the row) and both gdalbuildvrt
# and gdal_translate -projwin refuse such a raster. TE is the
# 'left bottom right top' bounds in the CRS of the dataset (build_bounds works in
# WGS84 degrees), -r near keeps the native resolution without resampling, and
# PREDICTOR=3 suits the Float32 store data. SRS is only passed for the stores that
# do not declare their own CRS: it is WGS 84 lat/lon with EGM2008 geoid heights.
SRS_FLAG := $(if $(SRS),-s_srs $(SRS))
clip:
	$(GDAL_CONFIG) gdalwarp -q -overwrite $(SRS_FLAG) -te $(TE) -r near -co TILED=YES -co COMPRESS=DEFLATE -co ZLEVEL=9 -co PREDICTOR=3 $(SOURCE) $(OUTPUT)

info:
	@echo 'Product folder: $(shell pwd)'
	@echo 'Dataset: $(DATASOURCE_URL)'
	@echo 'Local size: $(shell du -sh .)'

clean:
	@echo '$(PRODUCT) is a remote dataset, nothing to clean'

distclean: clean
	$(RM) Makefile

.DELETE_ON_ERROR:
.PHONY: all info clip clean distclean

#
# override most of make default behaviour
#
# disable make builtin rules
MAKEFLAGS += --no-builtin-rules
# disable suffix rules
.SUFFIXES:
