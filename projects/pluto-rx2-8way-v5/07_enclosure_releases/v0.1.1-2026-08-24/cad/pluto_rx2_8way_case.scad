/*
 * Support-free enclosure for pluto-rx2-8way-v5.
 *
 * Coordinates are case-local, with the PCB centered at the origin:
 *   +X = board right, +Y = five-SMA edge, +Z = component side.
 *
 * Export choices:
 *   openscad -o base.stl -D 'part="base"' this_file.scad
 *   openscad -o lid.stl -D 'part="lid"' this_file.scad
 *   openscad -o insert_coupon.stl -D 'part="insert_coupon"' this_file.scad
 */

part = "assembly";       // base, lid, insert_coupon, assembly
explode = 10;            // assembly-view lid lift, mm
show_reference_board = true;

$fn = 64;
eps = 0.05;

// Exact PCB datums from 04_kicad/pluto_rx2_8way_v5.kicad_pcb.
pcb_size = [90, 65];
pcb_thickness = 1.60;
mount_holes = [
    [-40, -27.5], [40, -27.5],
    [-40,  27.5], [40,  27.5]
];
north_sma_x = [-30, -15, 0, 15, 30];
side_sma_y = [4.5, -13.5];

// Printer-tunable parameters.
xy_clearance = 1.00;
wall = 2.40;
floor = 2.40;
roof = 2.40;
outer_radius = 4.40;
inner_radius = 2.00;

// E-Z LOK 260-M3-BR / 260-M3-CR nominal pocket.
insert_hole_d = 3.95;
insert_flange_recess_d = 6.10;
insert_flange_recess_depth = 0.80;
insert_length = 4.775;
insert_bottom_clearance = 0.30;
boss_d = 8.00;

// Board stack. Standoff height clears trimmed through-hole tails.
standoff_h = 5.40;
pcb_bottom_z = floor + standoff_h;
pcb_top_z = pcb_bottom_z + pcb_thickness;
sma_center_above_pcb = 10.30;
sma_top_above_pcb = 13.80;
seam_z = pcb_top_z + sma_center_above_pcb;
top_clearance = 1.50;
inner_roof_z = pcb_top_z + sma_top_above_pcb + top_clearance;
overall_z = inner_roof_z + roof;

// Connector access. The openings flare outward for SMA coupling-nut access.
sma_opening_inner_d = 10.20;
sma_opening_outer_d = 12.00;
usb_opening_w = 14.00;
usb_opening_bottom_z = pcb_bottom_z - 0.80;
usb_vertical_top_z = pcb_top_z + 2.60;
usb_arch_top_z = usb_vertical_top_z + 5.00;
usb_arch_flat_w = 4.00;

// Lid alignment and shared PCB/lid fasteners.
lip_h = 1.20;
lip_t = 0.80;
lip_clearance = 0.25;
lid_column_d = 7.20;
lid_column_board_gap = 0.15;
screw_clearance_d = 3.50;
screw_head_d = 6.30;
screw_length = 20.00;
// Keep the screw tip inside the threaded insert without bottoming out.
screw_tip_above_insert_bottom = 0.475;
// M3x20 tip lands 0.5 mm above the nominal blind-pocket bottom.
screw_seat_z = pcb_bottom_z - insert_length
             + screw_tip_above_insert_bottom + screw_length;

inner_size = [
    pcb_size[0] + 2 * xy_clearance,
    pcb_size[1] + 2 * xy_clearance
];
outer_size = [
    inner_size[0] + 2 * wall,
    inner_size[1] + 2 * wall
];

module rounded_rect_2d(size, radius) {
    offset(r = radius)
        square([size[0] - 2 * radius, size[1] - 2 * radius], center = true);
}

module shell_2d() {
    difference() {
        rounded_rect_2d(outer_size, outer_radius);
        rounded_rect_2d(inner_size, inner_radius);
    }
}

module base_alignment_lip() {
    // The lip overlaps the base wall by 0.20 mm so it is one solid. The lid
    // carries a matching, slightly larger lower-edge rabbet.
    lip_wall_overlap = 0.20;
    lip_outer_size = [
        inner_size[0] + 2 * lip_wall_overlap,
        inner_size[1] + 2 * lip_wall_overlap
    ];
    lip_inner_size = [
        inner_size[0] - 2 * lip_t,
        inner_size[1] - 2 * lip_t
    ];
    lip_outer_radius = inner_radius + lip_wall_overlap;
    lip_inner_radius = max(0.20, inner_radius - lip_t);

    translate([0, 0, seam_z - eps])
        linear_extrude(height = lip_h + eps)
            difference() {
                rounded_rect_2d(lip_outer_size, lip_outer_radius);
                rounded_rect_2d(lip_inner_size, lip_inner_radius);
            }
}

module lid_lip_rabbet() {
    lip_wall_overlap = 0.20;
    rabbet_size = [
        inner_size[0] + 2 * (lip_wall_overlap + lip_clearance),
        inner_size[1] + 2 * (lip_wall_overlap + lip_clearance)
    ];
    // Subtract only a perimeter band. Subtracting the whole enlarged cavity
    // here would slice through the four lid spacer columns at the seam.
    rabbet_inner_size = [
        inner_size[0] - 2 * (lip_t + 1.0),
        inner_size[1] - 2 * (lip_t + 1.0)
    ];
    rabbet_radius = inner_radius + lip_wall_overlap + lip_clearance;
    rabbet_inner_radius = max(0.20, inner_radius - lip_t - 1.0);

    translate([0, 0, seam_z - eps])
        linear_extrude(height = lip_h + 2 * eps)
            difference() {
                rounded_rect_2d(rabbet_size, rabbet_radius);
                rounded_rect_2d(rabbet_inner_size, rabbet_inner_radius);
            }
}

module axis_y_frustum(start_y, length, d_start, d_end) {
    translate([0, start_y, 0])
        rotate([-90, 0, 0])
            cylinder(h = length, d1 = d_start, d2 = d_end);
}

module axis_x_frustum(start_x, length, d_start, d_end, positive = true) {
    translate([start_x, 0, 0])
        rotate([0, positive ? 90 : -90, 0])
            cylinder(h = length, d1 = d_start, d2 = d_end);
}

module sma_cutouts() {
    board_x = pcb_size[0] / 2;
    board_y = pcb_size[1] / 2;
    outside_x = outer_size[0] / 2;
    outside_y = outer_size[1] / 2;

    for (x = north_sma_x)
        translate([x, 0, seam_z])
            axis_y_frustum(
                board_y - 1.0,
                outside_y - board_y + 2.0,
                sma_opening_inner_d,
                sma_opening_outer_d
            );

    for (y = side_sma_y) {
        translate([0, y, seam_z])
            axis_x_frustum(
                board_x - 1.0,
                outside_x - board_x + 2.0,
                sma_opening_inner_d,
                sma_opening_outer_d,
                true
            );
        translate([0, y, seam_z])
            axis_x_frustum(
                -board_x + 1.0,
                outside_x - board_x + 2.0,
                sma_opening_inner_d,
                sma_opening_outer_d,
                false
            );
    }
}

module usb_arch_cutout() {
    board_y = pcb_size[1] / 2;
    outside_y = outer_size[1] / 2;
    half_w = usb_opening_w / 2;
    half_flat = usb_arch_flat_w / 2;
    points = [
        [-half_w, usb_opening_bottom_z],
        [ half_w, usb_opening_bottom_z],
        [ half_w, usb_vertical_top_z],
        [ half_flat, usb_arch_top_z],
        [-half_flat, usb_arch_top_z],
        [-half_w, usb_vertical_top_z]
    ];

    translate([0, -board_y + 1.0, 0])
        rotate([90, 0, 0])
            linear_extrude(height = outside_y - board_y + 2.0)
                polygon(points);
}

module insert_pockets() {
    pocket_depth = insert_length + insert_bottom_clearance;
    for (p = mount_holes) {
        translate([p[0], p[1], pcb_bottom_z - pocket_depth])
            cylinder(h = pocket_depth + eps, d = insert_hole_d);
        translate([
            p[0], p[1],
            pcb_bottom_z - insert_flange_recess_depth
        ])
            cylinder(
                h = insert_flange_recess_depth + eps,
                d = insert_flange_recess_d
            );
    }
}

module base() {
    difference() {
        union() {
            linear_extrude(height = floor)
                rounded_rect_2d(outer_size, outer_radius);
            translate([0, 0, floor - eps])
                linear_extrude(height = seam_z - floor + eps)
                    shell_2d();
            for (p = mount_holes)
                translate([p[0], p[1], floor - eps])
                    cylinder(h = standoff_h + eps, d = boss_d);
            base_alignment_lip();
        }
        sma_cutouts();
        usb_arch_cutout();
        insert_pockets();
    }
}

module service_opening() {
    service_size = [24.0, 13.0];
    service_center = [-16.0, -23.8];
    translate([service_center[0], service_center[1], inner_roof_z - eps])
        linear_extrude(height = roof + 2 * eps)
            rounded_rect_2d(service_size, 2.0);
}

module lid_fastener_cuts() {
    for (p = mount_holes) {
        translate([p[0], p[1], pcb_top_z])
            cylinder(h = overall_z - pcb_top_z + eps, d = screw_clearance_d);
        translate([p[0], p[1], screw_seat_z])
            cylinder(h = overall_z - screw_seat_z + eps, d = screw_head_d);
    }
}

module lid_engraving() {
    north_names = ["ANT2", "ANT1", "RX", "ANT8", "ANT7"];
    west_names = ["ANT3", "ANT4"];
    east_names = ["ANT6", "ANT5"];

    translate([0, 9.5, overall_z - 0.45])
        linear_extrude(height = 0.50)
            text(
                "PLUTO RX2 8-WAY",
                size = 4.0,
                halign = "center",
                valign = "center",
                font = "Liberation Sans:style=Bold"
            );
    translate([-16.0, -15.8, overall_z - 0.45])
        linear_extrude(height = 0.50)
            text(
                "SWD / 5V",
                size = 2.8,
                halign = "center",
                valign = "center",
                font = "Liberation Sans:style=Bold"
            );

    for (i = [0 : len(north_sma_x) - 1])
        translate([north_sma_x[i], 27.2, overall_z - 0.45])
            linear_extrude(height = 0.50)
                text(
                    north_names[i],
                    size = 2.25,
                    halign = "center",
                    valign = "center",
                    font = "Liberation Sans:style=Bold"
                );

    for (i = [0 : len(side_sma_y) - 1]) {
        translate([-43.0, side_sma_y[i], overall_z - 0.45])
            linear_extrude(height = 0.50)
                rotate([0, 0, 90])
                    text(
                        west_names[i],
                        size = 2.25,
                        halign = "center",
                        valign = "center",
                        font = "Liberation Sans:style=Bold"
                    );
        translate([43.0, side_sma_y[i], overall_z - 0.45])
            linear_extrude(height = 0.50)
                rotate([0, 0, -90])
                    text(
                        east_names[i],
                        size = 2.25,
                        halign = "center",
                        valign = "center",
                        font = "Liberation Sans:style=Bold"
                    );
    }
}

module lid_final() {
    difference() {
        union() {
            translate([0, 0, seam_z])
                linear_extrude(height = inner_roof_z - seam_z + eps)
                    shell_2d();
            translate([0, 0, inner_roof_z])
                linear_extrude(height = roof)
                    rounded_rect_2d(outer_size, outer_radius);
            for (p = mount_holes)
                translate([
                    p[0], p[1],
                    pcb_top_z + lid_column_board_gap
                ])
                    cylinder(
                        h = inner_roof_z - pcb_top_z - lid_column_board_gap + eps,
                        d = lid_column_d
                    );
        }
        sma_cutouts();
        lid_lip_rabbet();
        service_opening();
        lid_fastener_cuts();
        lid_engraving();
    }
}

// Exported lid is exterior-face-down; pillars and walls grow upward.
module lid_print() {
    translate([0, 0, overall_z])
        rotate([180, 0, 0])
            lid_final();
}

module insert_coupon() {
    coupon_size = [54, 20];
    coupon_h = 6.0;
    coupon_radius = 2.0;
    sample_diameters = [4.15, 4.25, 4.35, 4.45];
    sample_x = [-20, -6.67, 6.67, 20];
    sample_y = 2.0;
    pocket_depth = insert_length + insert_bottom_clearance;

    difference() {
        union() {
            linear_extrude(height = coupon_h)
                rounded_rect_2d(coupon_size, coupon_radius);
            for (x = sample_x)
                translate([x, sample_y, 0])
                    cylinder(h = coupon_h, d = 10.0);
        }
        for (i = [0 : len(sample_diameters) - 1]) {
            translate([
                sample_x[i], sample_y,
                coupon_h - pocket_depth
            ])
                cylinder(h = pocket_depth + eps, d = sample_diameters[i]);
            translate([
                sample_x[i], sample_y,
                coupon_h - insert_flange_recess_depth
            ])
                cylinder(
                    h = insert_flange_recess_depth + eps,
                    d = insert_flange_recess_d
                );
            translate([sample_x[i], -6.0, coupon_h - 0.35])
                linear_extrude(height = 0.40)
                    text(
                        str(sample_diameters[i]),
                        size = 3.0,
                        halign = "center",
                        valign = "center",
                        font = "Liberation Sans:style=Bold"
                    );
        }
    }
}

module board_reference() {
    color([0.08, 0.34, 0.18])
        difference() {
            translate([-pcb_size[0] / 2, -pcb_size[1] / 2, pcb_bottom_z])
                cube([pcb_size[0], pcb_size[1], pcb_thickness]);
            for (p = mount_holes)
                translate([p[0], p[1], pcb_bottom_z - eps])
                    cylinder(h = pcb_thickness + 2 * eps, d = 3.20);
        }
}

module board_reference_interior() {
    // Remove 0.02 mm from each Z face so the deliberate support contact does
    // not appear as a zero-thickness, non-manifold "collision" in the check.
    color([0.08, 0.34, 0.18])
        difference() {
            translate([
                -pcb_size[0] / 2,
                -pcb_size[1] / 2,
                pcb_bottom_z + 0.02
            ])
                cube([pcb_size[0], pcb_size[1], pcb_thickness - 0.04]);
            for (p = mount_holes)
                translate([p[0], p[1], pcb_bottom_z - eps])
                    cylinder(h = pcb_thickness + 2 * eps, d = 3.20);
        }
}

module sma_reference_axis_y(x) {
    body_y = 20.9;
    z = pcb_top_z + sma_center_above_pcb;
    color([0.85, 0.62, 0.12]) {
        translate([x, body_y, z]) cube([7, 7, 7], center = true);
        translate([x, body_y + 2.5, z])
            rotate([-90, 0, 0])
                cylinder(h = pcb_size[1] / 2 - body_y + 1.0, d = 6.35);
    }
}

module sma_reference_axis_x(y, positive) {
    body_x = positive ? 33.4 : -33.4;
    z = pcb_top_z + sma_center_above_pcb;
    length = pcb_size[0] / 2 - abs(body_x) + 1.0;
    color([0.85, 0.62, 0.12]) {
        translate([body_x, y, z]) cube([7, 7, 7], center = true);
        translate([body_x + (positive ? 2.5 : -2.5), y, z])
            rotate([0, positive ? 90 : -90, 0])
                cylinder(h = length, d = 6.35);
    }
}

module component_references() {
    for (x = north_sma_x) sma_reference_axis_y(x);
    for (y = side_sma_y) {
        sma_reference_axis_x(y, true);
        sma_reference_axis_x(y, false);
    }

    // USB4105, J11 and J12 are simplified clearance witnesses.
    color([0.75, 0.75, 0.78])
        translate([-4.17, -pcb_size[1] / 2 - 0.55, pcb_top_z])
            cube([8.34, 8.94, 3.68]);
    color([0.15, 0.15, 0.16])
        translate([-24.6, -26.5, pcb_top_z]) cube([7.2, 7.2, 6.5]);
    color([0.12, 0.12, 0.12])
        translate([-14.1, -25.8, pcb_top_z]) cube([6.2, 3.0, 8.5]);
}

module assembly_view() {
    color([0.15, 0.18, 0.22]) base();
    if (show_reference_board) {
        board_reference();
        component_references();
    }
    color([0.25, 0.32, 0.40, 0.75])
        translate([0, 0, explode]) lid_final();
}

// Fixed non-exploded, enclosure-only collision/export selector.  Keep this
// free of PCB/component witnesses and keep lid geometry in installed rather
// than print orientation.
module installed_case() {
    union() {
        base();
        lid_final();
    }
}

// A successful clearance test exports no geometry. Contact at the four
// plastic support annuli is intentionally zero-thickness and therefore does
// not appear as a solid intersection.
module interference_check() {
    intersection() {
        union() {
            base();
            lid_final();
        }
        union() {
            board_reference_interior();
            component_references();
        }
    }
}

assert(insert_hole_d < insert_flange_recess_d,
       "Insert bore must be smaller than its flange recess");
assert(pcb_bottom_z - insert_length - insert_bottom_clearance > floor,
       "Insert pocket breaks through the case floor");
assert(screw_seat_z - screw_length >= pcb_bottom_z - insert_length,
       "M3x20 screw would run deeper than the nominal insert");
assert(screw_seat_z < inner_roof_z,
       "Screw-head seat must remain inside the roof-supported lid column");
assert(inner_roof_z >= pcb_top_z + sma_top_above_pcb + top_clearance,
       "Lid violates SMA top clearance");

if (part == "base") {
    base();
} else if (part == "lid") {
    lid_print();
} else if (part == "insert_coupon") {
    insert_coupon();
} else if (part == "installed_case") {
    installed_case();
} else if (part == "interference") {
    interference_check();
} else {
    assembly_view();
}
