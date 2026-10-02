
PRODUCT := {product}

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
	$(RM) $(PRODUCT).*.vrt
	$(RM) -r spool/*

distclean: clean
	$(RM) -r cache/* $(PRODUCT).vrt Makefile

.DELETE_ON_ERROR:
.PHONY: info clip clean distclean

#
# override most of make default behaviour
#
# disable make builtin rules
MAKEFLAGS += --no-builtin-rules
# disable suffix rules
.SUFFIXES:
