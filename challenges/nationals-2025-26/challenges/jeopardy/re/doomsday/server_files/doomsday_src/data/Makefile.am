
EXTRA_DIST=              \
        README           \
        doom.ico         \
        doom.png         \
        wadfile.png      \
        convert-icon

iconsdir = $(prefix)/share/icons/hicolor/128x128/apps
icons_DATA = doomsday.png 

doomsday.png : doom.png
	cp $(top_srcdir)/data/doom.png $@

CLEANFILES = $(icons_DATA)
