#!/bin/bash
# This script adds import statements for custom cipher keys to all example files

for example_file in toml_config/example.py ini_config/example.py yaml_config/example.py toml_config/example_advanced.py yaml_config/example_advanced.py ini_config/example_default_section.py; do
    echo "Processing $example_file..."

    # Check if the file already imports create_obscurer
    if ! grep -q "create_obscurer_from_passphrase" "$example_file"; then
        echo "  Adding import to $example_file"
    fi
done
