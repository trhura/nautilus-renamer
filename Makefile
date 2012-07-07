NAUTILUS_SCRIPTS_DIR = ~/.gnome2/nautilus-scripts

build:
	./scripts/genmo.py po/ mo/
	chmod +x nautilus-renamer.py

localinstall: build uninstall
	mkdir -p $(NAUTILUS_SCRIPTS_DIR)/.rdata/po
	cp -Rfv mo/* $(NAUTILUS_SCRIPTS_DIR)/.rdata/po
	cp -fv nautilus-renamer.py $(NAUTILUS_SCRIPTS_DIR)/Renamer

uninstall:
	rm -rfv $(NAUTILUS_SCRIPTS_DIR)/.rdata
	rm -rfv $(NAUTILUS_SCRIPTS_DIR)/Renamer

clean:
	rm -rfv mo
	rm -rfv .rope*
	find . -name '*.pyc' -exec rm '{}' \;
#find . -name '*~' -exec rm -rfv '{}' \;

.PHONY: clean localinstall uninstall
