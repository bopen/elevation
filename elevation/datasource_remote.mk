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

# nothing to prepare: the dataset is read in place by clip
all:
	@echo '$(PRODUCT) is a remote dataset, nothing to prepare'

# The crop is done with gdal_translate -projwin, as for the local products: it
# reads the remote dataset in place and returns the exact pixels of the store
# grid, without resampling and without shifting the output grid. PROJWIN is the
# 'left top right bottom' bounds in the CRS of the dataset (build_bounds works
# in WGS84 degrees) and PREDICTOR=3 suits the Float32 store data.
clip:
	gdal_translate -q -projwin $(PROJWIN) -co TILED=YES -co COMPRESS=DEFLATE -co ZLEVEL=9 -co PREDICTOR=3 $(SOURCE) $(OUTPUT)

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
