##
## Process this file with automake to produce Makefile.in
##

EXTRA_DIST = iksemel.c

if DO_IKSEMEL
iksemel_c = iksemel.c
endif

bin_PROGRAMS = omed

INCLUDES = -I$(top_srcdir)/include -I$(top_builddir)/include $(IKSEMEL_CFLAGS) $(SOURCEVIEW_CFLAGS) $(GTK_CFLAGS)
omed_LDADD = $(IKSEMEL_LIBS) $(SOURCEVIEW_LIBS) $(GTK_LIBS)

omed_SOURCES = \
	main.c \
	ui.c \
	om-tree.c \
	om-node.c \
	node-desc.c \
	node-acl.c \
	node-prop.c \
	node-oper.c \
	node-param.c \
	ui-util.c \
	csl-edit.c \
	export.c \
	iconv.c \
	my-combo.c \
	gtk-cell-combo.c \
	$(iksemel_c)
