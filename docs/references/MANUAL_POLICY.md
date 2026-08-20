# Vendor Manual Management Policy

Vendor manuals are an important part of the Instrument Automation
Platform knowledge system.

However, original vendor PDF files are treated as local reference
material and are not committed to Git by default.

Repository structure:

vendor_manuals/
  keysight/
    dsox3000/
  rohde_schwarz/
    fsw/

The vendor_manuals directory is ignored by Git.

The Git repository stores only structured metadata about manuals:

- manufacturer
- instrument family
- document title
- document type
- document number
- revision
- publication date
- filename
- SHA256
- official source
- notes

Knowledge flow:

Vendor Manual
-> Manual Registry
-> Command Catalog
-> Hardware Probe
-> Raw Response
-> Parser
-> Scenario Test
-> Qualification
-> Generated Documentation

The vendor manual remains the original vendor reference.

The verified command catalog and hardware results are the long-term
engineering knowledge assets of this repository.
