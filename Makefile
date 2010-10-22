NAUTILUS_SCRIPTS_DIR=~/.gnome2/nautilus-scripts
PREFIX=/usr

localinstall: uninstall 
	mkdir -p $(NAUTILUS_SCRIPTS_DIR)/.rdata
	cp -Rfv po  $(NAUTILUS_SCRIPTS_DIR)/.rdata/
	cp -Rfv icon $(NAUTILUS_SCRIPTS_DIR)/.rdata/

	cp -fv nautilus-renamer.py $(NAUTILUS_SCRIPTS_DIR)/Renamer

uninstall:
	rm -rf $(NAUTILUS_SCRIPTS_DIR)/.rdata
	rm -rf $(NAUTILUS_SCRIPTS_DIR)/Renamer

install:
	cp nautilus-renamer.py 
	mkdir  
clean:
	rm nautilus-renamer.pyc

.PHONY: all clean localinstall install