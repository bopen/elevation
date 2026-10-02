
PRODUCT := {product}

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
.PHONY: info clean distclean

#
# override most of make default behaviour
#
# disable make builtin rules
MAKEFLAGS += --no-builtin-rules
# disable suffix rules
.SUFFIXES:
