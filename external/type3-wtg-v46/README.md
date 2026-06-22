# Type-3 WTG V46 External Asset Staging

This directory is a local staging area for the official PSCAD Type-3 WTG V46 example.

Do not commit official PSCAD example files, model archives, extracted `.pscx` / `.pslx` / `.psl` / `.lib` files, generated binaries, or run outputs to Git unless the user has separately confirmed redistribution rights.

## Official Source

Use the PSCAD official knowledge-base entry:

`https://www.pscad.com/knowledge-base/article/496`

Page title:

`Type 3 Wind Turbine Generators (WTG) (for PSCAD v4.6)`

The official page lists the example as:

`Type 3 Wind Turbine Model - V46`

## Recommended Local Layout

Use this structure:

```text
external/type3-wtg-v46/
|-- ORIGINAL_DOWNLOAD_DO_NOT_EDIT/
|-- WORKING_COPY/
|-- README.md
|-- source_manifest_template.yaml
```

Put the original downloaded archive and its first extraction in:

`external/type3-wtg-v46/ORIGINAL_DOWNLOAD_DO_NOT_EDIT/`

Then copy the entire extracted folder into:

`external/type3-wtg-v46/WORKING_COPY/`

Open only the working copy in PSCAD.

## File Handling Rules

- Keep all downloaded and extracted official files out of Git.
- Keep related PSCAD files together. Do not move only the `.pscx` file and leave libraries or support files behind.
- If PSCAD asks to convert a project version, convert only the working copy.
- Do not connect the Type-3 model to the 3IBR project during this acquisition stage.
- Run the Type-3 example independently before any future replacement experiment.

## Version Check

Before opening in PSCAD, confirm from the official page or included documentation that the package is the V46 / PSCAD v4.6-compatible Type-3 wind turbine model.

After download, fill:

`external/type3-wtg-v46/source_manifest_template.yaml`

Record filename, source URL, size, SHA-256, download date, and any MyCentre or license notice shown during access.
