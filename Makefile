NAUTILUS_SCRIPTS_DIR = "$(HOME)/.local/share/nautilus-renamer"

build:
	./scripts/genmo.py po/ mo/
	chmod +x nautilus-renamer.py

localinstall: build uninstall
	mkdir -p $(NAUTILUS_SCRIPTS_DIR)/.rdata/po
	cp -Rfv mo/* $(NAUTILUS_SCRIPTS_DIR)/.rdata/po
	cp -fv nautilus-renamer.py $(NAUTILUS_SCRIPTS_DIR)/Renamer
	dconf write  '/org/gnome/nautilus/preferences/bulk-rename-tool' "b'$(NAUTILUS_SCRIPTS_DIR)/Renamer'"

uninstall:
	rm -rfv $(NAUTILUS_SCRIPTS_DIR)/.rdata
	rm -rfv $(NAUTILUS_SCRIPTS_DIR)/Renamer
	dconf reset  '/org/gnome/nautilus/preferences/bulk-rename-tool'

clean:
	rm -rfv mo
	rm -rfv .rope*
	find . -name '*.pyc' -exec rm '{}' \;

.PHONY: clean localinstall uninstall
