# Type-3 WTG Official Source Audit

Date: 2026-06-22

## Audited Source

Official PSCAD knowledge-base page:

`https://www.pscad.com/knowledge-base/article/496`

Official page title:

`Type 3 Wind Turbine Generators (WTG) (for PSCAD v4.6)`

## Compatibility Finding

The official page lists `v4.6.2` under applicable versions. It also lists adjacent PSCAD X4 and PSCAD v5 versions, including `v4.6.0`, `v4.6.1`, `v4.6.3`, `v5.0.0`, `v5.0.1`, `v5.0.2`, and `v5.1.0`.

This is compatible with the current environment target: PSCAD X4 v4.6.2 Professional.

## Model Content Claimed by Official Page

The official page states that the example includes:

- Average and detailed Type-3 wind turbine models.
- Mechanical components including pitch controller and wind turbine.
- Electrical components.
- Rotor-side converter and controller.
- Grid-side converter and controllers.
- DC-link system, including chopper.
- Low-pass filter.
- Crowbar protection.
- Scaling component for aggregated wind turbine units or a wind farm.

The public technical PDF also identifies the model as a PSCAD v4.6 Type-3 wind turbine model and describes the Type-3 WTG as a DFIG model with mechanical and electrical subsystems.

## Official Download Entrypoints

The official page lists:

- Document: `Technical Specification - Type 3 Wind Turbine Model - V46`
- Example: `Type 3 Wind Turbine Model - V46`

The technical specification PDF was publicly reachable during audit:

`https://www.pscad.com/knowledge-base/download/type_3_wind_turbine_model.pdf`

The example model should be obtained only through the official `Examples` link on the PSCAD page. Do not use forum attachments, cloud-drive mirrors, cracked packages, or unofficial GitHub repositories.

## Access Status

The official page itself and the technical PDF are publicly readable. The example model entry is an official PSCAD download entrypoint. If the example link redirects to MyCentre, requires login, or requires entitlement/maintenance permissions, the user must complete that access flow manually using their PSCAD account and license rights.

No bypass, scraping of restricted assets, credential workaround, or third-party mirror is allowed.

## Expected File Identity After Manual Download

Because the model archive was not downloaded automatically into this repository, the exact archive filename and checksum remain unverified. After manual download, record:

- Download URL shown by the browser.
- Archive filename.
- Archive size.
- SHA-256 hash.
- Download date.
- Any license or access notice shown by PSCAD/MyCentre.

Use `external/type3-wtg-v46/source_manifest_template.yaml` for this record.

## Official-Source Conclusion

The preferred legal acquisition route is the PSCAD official knowledge-base page above. The page explicitly identifies the Type-3 WTG V46 example and lists PSCAD v4.6.2 as an applicable version. The current project must not commit or redistribute the downloaded official PSCAD example files unless redistribution rights are separately confirmed by the user.
