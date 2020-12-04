
DATASOURCE_URL := {datasource_url}
PRODUCT := {product}
TILE_EXT := {tile_ext}
FTW_EXT := .tfw
COMPRESSED_PRE_EXT = {compressed_pre_ext}
COMPRESSED_EXT := {compressed_ext}

ENSURE_TILE_PATHS := $(foreach n,$(ENSURE_TILES),cache/$n)
STDERR_SWITCH := 2>/dev/null

$(info  DEM files covered $(ENSURE_TILES))

all: $(PRODUCT).vrt

$(PRODUCT).vrt: $(shell find cache -size +0 -name "*.tif" 2>/dev/null)
	gdalbuildvrt -q -overwrite $@ $^

spool/%$(COMPRESSED_EXT):
	@mkdir -p $(dir $@)
	curl -s -o $@.temp $(DATASOURCE_URL)/$*$(COMPRESSED_EXT) && mv $@.temp $@

spool/%$(TILE_EXT): spool/%$(COMPRESSED_PRE_EXT).zip
	unzip -qq -d spool $< $*$(TILE_EXT) $*$(FTW_EXT) $(STDERR_SWITCH) || touch $@
	mv spool/$*$(FTW_EXT) cache/

spool/%$(TILE_EXT): spool/%$(COMPRESSED_PRE_EXT).gz
	gunzip $< $(STDERR_SWITCH) || touch $@

cache/%.tif: spool/%$(TILE_EXT)
	@mkdir -p $(dir $@)
	gdal_translate -q -co TILED=YES -co COMPRESS=DEFLATE -co ZLEVEL=9 -co PREDICTOR=2 $< $@ $(STDERR_SWITCH) || touch $@

download: $(ENSURE_TILE_PATHS)

copy_vrt:
	cp $(PRODUCT).vrt $(PRODUCT).$(RUN_ID).vrt

clip: $(PRODUCT).vrt
	gdal_translate -q -co TILED=YES -co COMPRESS=DEFLATE -co ZLEVEL=9 -co PREDICTOR=2 -projwin $(PROJWIN) $(PRODUCT).$(RUN_ID).vrt $(OUTPUT)
	$(RM) $(PRODUCT).$(RUN_ID).vrt

info:
	@echo 'Product folder: $(shell pwd)'
	@echo 'Tiles count: $(shell ls cache/*.tif | wc -l)'
	@echo 'Cache size: $(shell du -sh .)'

clean:
	find cache -size 0 -name "*.tif" -delete
	find cache -size 0 -name "*.tfw" -delete
	$(RM) $(PRODUCT).*.vrt
	$(RM) -r spool/*

distclean: clean
	$(RM) cache/* $(PRODUCT).vrt Makefile

.DELETE_ON_ERROR:
.PHONY: all info download clip clean distclean

#
# override most of make default behaviour
#
# disable make builtin rules
MAKEFLAGS += --no-builtin-rules
# disable suffix rules
.SUFFIXES:
