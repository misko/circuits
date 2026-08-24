# Enclosure topology selection

Choose topology from connector distribution, serviceability, print orientation, and fastening—not aesthetics alone.

The built-in v1 engine accepts one axis-aligned rectangular PCB outline. It does not approximate irregular contours, internal cutouts, or multiple outline islands. Stop and create a reviewed CAD adapter for those boards.

## Split shell

Use `split_shell` when most edge connectors can cross one horizontal seam and a base plus lid gives direct board access.

- Printable parts are normally `base`, `lid`, and `insert_coupon`.
- Place `seam_z_mm` through the useful connector-opening band while keeping it strictly inside the cavity.
- Keep the lower shell deep enough for insert pockets, board standoffs, and solder-side clearance.
- Keep the upper shell high enough for fitted components, plug strain relief, and screw-head recesses.
- Orient base and lid on their broad exterior faces. Shape lips and recesses so neither part needs trapped support.

Prefer this topology for sparse or uniform edge I/O. Avoid it when many connector openings would become fragile half-holes, when replaceable panels are valuable, or when PCB revisions are expected to move edge I/O.

## Base, lid, and captured panels

Use `base_lid_panels` when connectors populate several edges, panel iteration should not require reprinting the shell, or edge openings are too intricate for a clean seam.

- Printable parts include base, lid, insert coupon when required, and all four captured panels; a deliberately closed edge uses a panel without openings.
- Set `panel_capture_mm` for positive retention and `panel_clearance_mm` for printable sliding fit.
- Keep capture grooves open in the chosen print orientation.
- Put connector geometry in panels; keep base and lid structurally regular.
- Ensure every panel can be installed in a defined assembly order and cannot escape after lid fastening.

Prefer separate perimeter fasteners when lid retention should not load PCB holes. Check that the corner posts do not crowd the board or connector backshells.

## Fastener strategy

Use `shared_board` when the same screws can retain lid, PCB, and inserts without excessive unsupported length, board stress, or ambiguous stack-up. Confirm lid screw engagement and tip clearance across the full stack.

Use `separate_perimeter` when board mounting and lid retention need independent service, when PCB holes are poorly located for shell closure, or when the enclosure is large. Provide at least four case-hole locations and validate both screw stacks.

## Selection record

Before generation, record:

- chosen topology and rejected alternative;
- board insertion and removal path;
- panel/lid assembly order;
- printable orientation for every part;
- support exceptions, if any;
- insert installation direction;
- cable and tool approach directions;
- seams that cross openings, vents, or gasket paths.

Treat these as mechanical design decisions. The generator validates represented dimensions, but it cannot infer assembly accessibility or whether a human can install the hardware.
