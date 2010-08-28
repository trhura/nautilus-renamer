#!/bin/bash

## Installer for Renamer

DIR=~/.gnome2/nautilus-scripts
sleep 1
echo
echo "---------------------"
echo "Installer for Renamer"
echo "---------------------"
echo
sleep 1

echo "Info"
echo "----"
echo -n "Current user: "; whoami
echo "Renamer will be installed in "$DIR
echo "Icons and readme will be stored in $DIR/.rdata"
echo
sleep 1

echo "--------------------------------------------------"
echo "DEPENDENCIES --> \"pyGTK\" and \"python-notify\"."
echo "Make sure you got those packages to use this script."
echo "--------------------------------------------------"
sleep 2

echo "Installing Icons and Locales"
echo "----------------"
# Clean up previous installations
rm -rf "$DIR/.rdata"
rm -rf "$DIR/Renamer"

mkdir -p "$DIR/.rdata"
cp -Rfv po  "$DIR/.rdata/"
cp -Rfv icon "$DIR/.rdata/"
echo 
echo "Installing script"
echo "-----------------"
cp -fv Renamer "$DIR/"
echo
sleep 1
echo "----------------------"
echo "Installation Finished"
echo "----------------------"
