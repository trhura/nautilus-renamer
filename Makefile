NAUTILUS_SCRIPTS_DIR = ~/.gnome2/nautilus-scripts

install: uninstall 
	mkdir -p $(NAUTILUS_SCRIPTS_DIR)/.rdata 
	./scripts/genmo.py po/ $(NAUTILUS_SCRIPTS_DIR)/.rdata/po/	
	cp -fv nautilus-renamer.py $(NAUTILUS_SCRIPTS_DIR)/Renamer

globalinstall:
	./scripts/install

uninstall:
	rm -rf $(NAUTILUS_SCRIPTS_DIR)/.rdata
	rm -rf $(NAUTILUS_SCRIPTS_DIR)/Renamer

.PHONY: all clean install
