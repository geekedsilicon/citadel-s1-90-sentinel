#!/usr/bin/env python3
"""
==============================================================================
VAELIX | SENTINEL MARK I — PINOUT AUTO-SYNC SCRIPT
==============================================================================
FILE:      scripts/update_pinout.py
VERSION:   1.0.0
PURPOSE:   Parse Verilator XML output and update README.md pinout table

USAGE:
    python3 scripts/update_pinout.py <xml_file> <readme_file>

PROCESS:
    1. Parse Verilator XML to extract top-level module IO ports
    2. Generate markdown table from port definitions
    3. Update 'Pinout Table' section in README.md using regex replacement
==============================================================================
"""

import sys
import re
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_verilator_xml(xml_path):
    """
    Parse Verilator XML output and extract port information.
    
    Returns:
        list of dicts: [{'name': 'ui_in', 'dir': 'input', 'width': 8}, ...]
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    # First, build a type table from the typetable section
    type_table = {}
    typetable = root.find('.//typetable')
    if typetable is not None:
        for dtype in typetable.findall('basicdtype'):
            dtype_id = dtype.get('id')
            left = dtype.get('left', None)
            right = dtype.get('right', None)
            
            if left is not None and right is not None:
                try:
                    width = abs(int(left) - int(right)) + 1
                except ValueError:
                    width = 1
            else:
                width = 1
            
            type_table[dtype_id] = width
    
    ports = []
    
    # Find the top-level module (has topModule="1" attribute)
    for module in root.findall('.//module'):
        # Check if this is the top module
        is_top = module.get('topModule') == '1'
        if not is_top:
            continue
        
        # Extract all var elements with dir attribute (these are ports)
        for var in module.findall('var'):
            port_dir = var.get('dir')
            if port_dir is None:
                continue  # Not a port, just an internal variable
            
            port_name = var.get('name', '')
            dtype_id = var.get('dtype_id', '2')
            
            # Look up width from type table
            width = type_table.get(dtype_id, 1)
            
            ports.append({
                'name': port_name,
                'direction': port_dir,
                'width': width
            })
        
        # Only process first top module
        break
    
    return ports


def generate_pinout_table(ports):
    """
    Generate markdown table from port list.
    
    Args:
        ports: list of port dicts
        
    Returns:
        str: Markdown table as string
    """
    if not ports:
        return "No ports found.\n"
    
    # Create table header
    lines = [
        "| Port Name | Direction | Width | Description |",
        "|-----------|-----------|-------|-------------|"
    ]
    
    # Map port names to descriptions based on common Tiny Tapeout conventions
    descriptions = {
        'ui_in': 'Dedicated inputs — Key Interface',
        'uo_out': 'Dedicated outputs — Display Interface',
        'uio_in': 'IOs: Input path — Secondary Telemetry',
        'uio_out': 'IOs: Output path — Status Array',
        'uio_oe': 'IOs: Enable path — Port Directional Control',
        'ena': 'Power-state enable',
        'clk': 'System Clock',
        'rst_n': 'Global Reset (Active LOW)'
    }
    
    # Add each port
    for port in ports:
        name = port['name']
        direction = port['direction']
        width = port['width']
        desc = descriptions.get(name, '—')
        
        # Format width display
        if width > 1:
            width_str = f"[{width-1}:0]"
        else:
            width_str = "1"
        
        lines.append(f"| `{name}` | {direction} | {width_str} | {desc} |")
    
    return '\n'.join(lines) + '\n'


def update_readme(readme_path, pinout_table):
    """
    Update the Pinout Table section in README.md.
    
    Args:
        readme_path: Path to README.md
        pinout_table: Markdown table string to insert
    """
    readme_path = Path(readme_path)
    
    if not readme_path.exists():
        print(f"ERROR: README file not found at {readme_path}")
        sys.exit(1)
    
    content = readme_path.read_text()
    
    # Define the section markers
    section_start = "<!-- BEGIN PINOUT TABLE -->"
    section_end = "<!-- END PINOUT TABLE -->"
    
    # Check if markers exist
    if section_start in content and section_end in content:
        # Replace existing content between markers
        pattern = re.compile(
            f"{re.escape(section_start)}.*?{re.escape(section_end)}",
            re.DOTALL
        )
        new_section = f"{section_start}\n{pinout_table}{section_end}"
        updated_content = pattern.sub(new_section, content)
    else:
        # Add new section after "OPERATIONAL INTERFACE" section
        # Look for the section header
        interface_pattern = r"(## 03 \| OPERATIONAL INTERFACE\n)"
        
        if re.search(interface_pattern, content):
            # Insert after the OPERATIONAL INTERFACE section
            new_section = f"\n### Pinout Table\n{section_start}\n{pinout_table}{section_end}\n"
            updated_content = re.sub(
                interface_pattern,
                r"\1" + new_section,
                content,
                count=1
            )
        else:
            # Fallback: append at end
            new_section = f"\n\n## Pinout Table\n{section_start}\n{pinout_table}{section_end}\n"
            updated_content = content + new_section
    
    # Write back to file
    readme_path.write_text(updated_content)
    print(f"✓ Updated {readme_path}")


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 update_pinout.py <xml_file> <readme_file>")
        sys.exit(1)
    
    xml_file = sys.argv[1]
    readme_file = sys.argv[2]
    
    print(f"Parsing Verilator XML: {xml_file}")
    ports = parse_verilator_xml(xml_file)
    
    print(f"Found {len(ports)} ports")
    for port in ports:
        print(f"  - {port['name']}: {port['direction']} [{port['width']}-bit]")
    
    print("Generating pinout table...")
    table = generate_pinout_table(ports)
    
    print("Updating README.md...")
    update_readme(readme_file, table)
    
    print("✓ Pinout synchronization complete")


if __name__ == '__main__':
    main()
