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
 *   openscad -o rx2_antenna_clip.stl \
 *       -D 'part="rx2_antenna_clip"' this_file.scad
 *   openscad -o rx2_clip_fit_coupon.stl \
 *       -D 'part="rx2_clip_fit_coupon"' this_file.scad
 */

part = "assembly";
explode = 10;            // assembly-view lid lift, mm
clip_explode = 8;        // additional clip lift above the exploded lid, mm
show_reference_board = true;
show_reference_antenna = true;
show_fastener_references = true;

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
insert_hole_d = 4.25;
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

// Shared top service opening.
service_size = [24.0, 13.0];
service_center = [-16.0, -23.8];

// Separate RX2/reference antenna clip.  The two additional inserts are the
// same E-Z LOK 260-M3-BR/CR cold-press family and the same coupon-qualified
// 4.25 mm production pilot as the four board fasteners above.
clip_mount_points = [[-22.0, 8.0], [22.0, 8.0]];
clip_boss_drop = 3.50;
clip_boss_bottom_d = 9.00;
clip_boss_roof_d = 12.00;
clip_plate_h = 3.20;
clip_head_recess_depth = 0.50;
clip_screw_length = 8.00;       // M3 x 8 socket-head cap screw
clip_insert_bottom_z = inner_roof_z - clip_boss_drop;
clip_insert_top_z = clip_insert_bottom_z + insert_length;
clip_screw_bearing_z = overall_z + clip_plate_h - clip_head_recess_depth;
clip_screw_nonthread_z = clip_screw_bearing_z - clip_insert_top_z;
clip_screw_engagement = clip_screw_length - clip_screw_nonthread_z;
clip_screw_tip_clearance = insert_length - clip_screw_engagement;
clip_insert_roof_skin = overall_z - (
    clip_insert_bottom_z + insert_length + insert_bottom_clearance
);

clip_main_size = [64.0, 28.0];
clip_main_center = [0.0, 10.0];
clip_tail_size = [39.0, 20.0];
clip_tail_center = [16.5, -8.0];
clip_candidate_body_d = 10.0;
clip_body_clearance = 0.15;
clip_arm_wall = 1.80;
clip_snap_lip = 0.90;
clip_station_length = 4.0;
clip_station_y = [9.0, 19.0];

// RG316-class routing witness only: 2.5 mm OD and 15 mm centerline bend
// radius.  Verify the actual pigtail data before relying on these values.
coax_candidate_d = 2.50;
coax_clearance = 0.25;
coax_guide_wall = 1.40;
coax_guide_height = 6.50;
coax_bend_radius = 15.0;
coax_straight_end_x = 34.0;

antenna_label_size = 4.20;
clip_fit_diameters = [9.0, 9.5, 10.0, 10.5];

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

module clip_plate_2d() {
    union() {
        translate(clip_main_center)
            rounded_rect_2d(clip_main_size, 3.0);
        translate(clip_tail_center)
            rounded_rect_2d(clip_tail_size, 2.0);
    }
}

module annular_sector_2d(r_inner, r_outer, angle_start, angle_end, step = 5) {
    polygon(concat(
        [for (a = [angle_start : step : angle_end])
            [r_outer * cos(a), r_outer * sin(a)]],
        [for (a = [angle_end : -step : angle_start])
            [r_inner * cos(a), r_inner * sin(a)]]
    ));
}

// Open-top snap station for a horizontal cylindrical body whose axis is +Y.
// Vertical arms and 45-degree triangular lips grow support-free from base_z.
module snap_station_axis_y(
    body_d,
    station_length,
    base_z,
    center_y,
    clearance = clip_body_clearance,
    arm_wall = clip_arm_wall,
    snap_lip = clip_snap_lip
) {
    inner_x = body_d / 2 + clearance;
    arm_h = body_d * 0.78;
    lip_z0 = body_d * 0.54;
    lip_zm = body_d * 0.64;
    lip_z1 = body_d * 0.78;

    translate([inner_x, center_y - station_length / 2, base_z - eps])
        cube([arm_wall, station_length, arm_h + eps]);
    translate([-inner_x - arm_wall, center_y - station_length / 2, base_z - eps])
        cube([arm_wall, station_length, arm_h + eps]);

    translate([0, center_y + station_length / 2, base_z])
        rotate([90, 0, 0])
            linear_extrude(height = station_length)
                polygon([
                    [inner_x + eps, lip_z0],
                    [inner_x + eps, lip_z1],
                    [inner_x - snap_lip, lip_zm]
                ]);
    translate([0, center_y + station_length / 2, base_z])
        rotate([90, 0, 0])
            linear_extrude(height = station_length)
                polygon([
                    [-inner_x - eps, lip_z0],
                    [-inner_x + snap_lip, lip_zm],
                    [-inner_x - eps, lip_z1]
                ]);
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

module lid_clip_bosses() {
    for (p = clip_mount_points)
        translate([p[0], p[1], clip_insert_bottom_z])
            cylinder(
                h = clip_boss_drop + eps,
                d1 = clip_boss_bottom_d,
                d2 = clip_boss_roof_d
            );
}

module lid_clip_fastener_cuts() {
    pocket_depth = insert_length + insert_bottom_clearance;
    for (p = clip_mount_points) {
        // Insert enters from the lid underside.  Its flange therefore reacts
        // an upward antenna pull into the boss rather than pulling out.
        translate([p[0], p[1], clip_insert_bottom_z - eps])
            cylinder(h = pocket_depth + 2 * eps, d = insert_hole_d);
        translate([p[0], p[1], clip_insert_bottom_z - eps])
            cylinder(
                h = insert_flange_recess_depth + eps,
                d = insert_flange_recess_d
            );
        translate([
            p[0], p[1],
            clip_insert_bottom_z + pocket_depth - eps
        ])
            cylinder(
                h = overall_z - clip_insert_bottom_z - pocket_depth + 2 * eps,
                d = screw_clearance_d
            );
    }
}

module lid_engraving() {
    north_names = ["A2", "A1", "RX", "A8", "A7"];
    west_names = ["A3", "A4"];
    east_names = ["A6", "A5"];

    translate([20.0, -27.0, overall_z - 0.45])
        linear_extrude(height = 0.50)
            text(
                "PLUTO 8-WAY",
                size = 3.2,
                halign = "center",
                valign = "center",
                font = "Liberation Sans:style=Bold"
            );
    translate([-37.0, -23.8, overall_z - 0.45])
        linear_extrude(height = 0.50)
            rotate([0, 0, 90])
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
                    size = north_names[i] == "RX" ? 3.0 : antenna_label_size,
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
                        size = antenna_label_size,
                        halign = "center",
                        valign = "center",
                        font = "Liberation Sans:style=Bold"
                    );
        translate([43.0, side_sma_y[i], overall_z - 0.45])
            linear_extrude(height = 0.50)
                rotate([0, 0, -90])
                    text(
                        east_names[i],
                        size = antenna_label_size,
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
            lid_clip_bosses();
        }
        sma_cutouts();
        lid_lip_rabbet();
        service_opening();
        lid_fastener_cuts();
        lid_clip_fastener_cuts();
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

module clip_cable_guides() {
    coax_inner = coax_candidate_d / 2 + coax_clearance;
    rail_offset = coax_inner + coax_guide_wall / 2;

    // Short straight section from the antenna body into the deliberate
    // 15 mm-radius bend.
    for (side = [-1, 1])
        translate([
            side * rail_offset - coax_guide_wall / 2,
            -0.20,
            clip_plate_h - eps
        ])
            cube([coax_guide_wall, 4.40, coax_guide_height + eps]);

    // Two concentric support-free vertical rails define the 90-degree bend.
    for (side = [-1, 1]) {
        rail_r = coax_bend_radius + side * rail_offset;
        translate([15.0, 0.0, clip_plate_h - eps])
            linear_extrude(height = coax_guide_height + eps)
                annular_sector_2d(
                    rail_r - coax_guide_wall / 2,
                    rail_r + coax_guide_wall / 2,
                    180,
                    270
                );
    }

    // Exit toward the east edge of the clip tail.
    for (side = [-1, 1])
        translate([
            14.80,
            -15.0 + side * rail_offset - coax_guide_wall / 2,
            clip_plate_h - eps
        ])
            cube([
                coax_straight_end_x - 14.60,
                coax_guide_wall,
                coax_guide_height + eps
            ]);

    // A second open-top snap station after the bend is the axial strain
    // relief.  It reacts cable pull into the clip rather than the Pluto SMA.
    translate([29.0, -15.0, 0])
        rotate([0, 0, 90])
            snap_station_axis_y(
                coax_candidate_d,
                5.0,
                clip_plate_h + clip_candidate_body_d / 2
                    - coax_candidate_d / 2,
                0,
                coax_clearance,
                coax_guide_wall,
                0.45
            );
}

module clip_labels() {
    translate([-19.0, 17.0, clip_plate_h - 0.45])
        linear_extrude(height = 0.50)
            text(
                "RX2",
                size = 3.4,
                halign = "center",
                valign = "center",
                font = "Liberation Sans:style=Bold"
            );
    translate([18.0, 17.0, clip_plate_h - 0.45])
        linear_extrude(height = 0.50)
            text(
                "REFERENCE",
                size = 2.8,
                halign = "center",
                valign = "center",
                font = "Liberation Sans:style=Bold"
            );
}

module rx2_antenna_clip() {
    difference() {
        union() {
            linear_extrude(height = clip_plate_h)
                clip_plate_2d();
            for (y = clip_station_y)
                snap_station_axis_y(
                    clip_candidate_body_d,
                    clip_station_length,
                    clip_plate_h,
                    y
                );
            clip_cable_guides();
        }

        // M3 clearance bores and shallow locating recesses for the M3x8
        // socket heads.  The heads remain deliberately proud and accessible.
        for (p = clip_mount_points) {
            translate([p[0], p[1], -eps])
                cylinder(h = clip_plate_h + 2 * eps, d = screw_clearance_d);
            translate([
                p[0], p[1],
                clip_plate_h - clip_head_recess_depth
            ])
                cylinder(
                    h = clip_head_recess_depth + eps,
                    d = screw_head_d
                );
        }
        clip_labels();
    }
}

module rx2_clip_fit_coupon() {
    coupon_size = [80.0, 24.0];
    coupon_h = 2.40;
    coupon_x = [-29.0, -9.67, 9.67, 29.0];

    difference() {
        union() {
            linear_extrude(height = coupon_h)
                rounded_rect_2d(coupon_size, 2.0);
            for (i = [0 : len(clip_fit_diameters) - 1])
                translate([coupon_x[i], 0, 0])
                    snap_station_axis_y(
                        clip_fit_diameters[i],
                        5.0,
                        coupon_h,
                        2.0
                    );
        }
        for (i = [0 : len(clip_fit_diameters) - 1])
            translate([coupon_x[i], -7.0, coupon_h - 0.35])
                linear_extrude(height = 0.40)
                    text(
                        str(clip_fit_diameters[i]),
                        size = 3.0,
                        halign = "center",
                        valign = "center",
                        font = "Liberation Sans:style=Bold"
                    );
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

module rx2_reference_antenna() {
    antenna_axis_z = clip_plate_h + clip_candidate_body_d / 2;

    // Candidate 10 mm right-angle antenna body based only on legacy SPF
    // fixture geometry.  The fit coupon, not this witness, decides real fit.
    color([0.10, 0.10, 0.11]) {
        translate([0, 4.0, antenna_axis_z])
            rotate([-90, 0, 0])
                cylinder(h = 20.0, d = clip_candidate_body_d);
        translate([0, 24.0, antenna_axis_z])
            cylinder(h = 34.0, d = 8.25);
    }

    // SMA coupling witness; gender and exact nut geometry remain unverified.
    color([0.78, 0.62, 0.20])
        translate([0, 0, antenna_axis_z])
            rotate([-90, 0, 0])
                cylinder(h = 4.0, d = 8.0);

    // RG316-class routing witness: no less than 15 mm centerline radius.
    color([0.20, 0.20, 0.22]) {
        translate([15.0, 0.0, antenna_axis_z])
            rotate([0, 0, 180])
                rotate_extrude(angle = 90, convexity = 10)
                    translate([coax_bend_radius, 0, 0])
                        circle(d = coax_candidate_d);
        translate([15.0, -15.0, antenna_axis_z])
            rotate([0, 90, 0])
                cylinder(
                    h = coax_straight_end_x - 15.0,
                    d = coax_candidate_d
                );
    }
}

module clip_insert_references(lid_shift = 0) {
    color([0.76, 0.52, 0.16])
        for (p = clip_mount_points) {
            translate([
                p[0], p[1],
                clip_insert_bottom_z + lid_shift
            ])
                cylinder(h = insert_length, d = 4.216);
            translate([
                p[0], p[1],
                clip_insert_bottom_z + lid_shift
            ])
                cylinder(h = insert_flange_recess_depth, d = 5.537);
        }
}

module clip_screw_references(clip_shift = 0) {
    color([0.50, 0.53, 0.56])
        for (p = clip_mount_points) {
            translate([
                p[0], p[1],
                clip_screw_bearing_z - clip_screw_length + clip_shift
            ])
                cylinder(h = clip_screw_length, d = 3.0);
            translate([
                p[0], p[1],
                clip_screw_bearing_z + clip_shift
            ])
                cylinder(h = 3.0, d = 5.5);
        }
}

module assembly_view() {
    color([0.15, 0.18, 0.22]) base();
    if (show_reference_board) {
        board_reference();
        component_references();
    }
    color([0.25, 0.32, 0.40, 0.75])
        translate([0, 0, explode]) lid_final();
    color([0.19, 0.42, 0.62])
        translate([0, 0, overall_z + explode + clip_explode])
            rx2_antenna_clip();
    if (show_reference_antenna)
        translate([0, 0, overall_z + explode + clip_explode])
            rx2_reference_antenna();
    if (show_fastener_references) {
        clip_insert_references(explode);
        clip_screw_references(explode + clip_explode);
    }
}

// Fixed non-exploded, enclosure-only collision/export selector.  Keep this
// free of PCB/component witnesses and keep lid geometry in installed rather
// than print orientation.
module installed_case() {
    union() {
        base();
        lid_final();
        translate([0, 0, overall_z - eps])
            rx2_antenna_clip();
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
assert((clip_boss_bottom_d - insert_flange_recess_d) / 2 >= 0.90,
       "RX2 clip insert boss violates 0.90 mm minimum radial wall");
assert(clip_insert_roof_skin >= 0.80,
       "RX2 clip insert pocket leaves less than 0.80 mm roof skin");
assert(clip_screw_engagement >= 4.00,
       "M3x8 RX2 clip screw has less than 4.00 mm insert engagement");
assert(clip_screw_tip_clearance >= 0.20,
       "M3x8 RX2 clip screw would bottom in the insert");
assert(
    (clip_tail_center[0] - clip_tail_size[0] / 2)
        - (service_center[0] + service_size[0] / 2) >= 1.00,
    "RX2 clip tail encroaches on the removable-lid service opening"
);
assert(
    27.2 - antenna_label_size / 2
        - (clip_main_center[1] + clip_main_size[1] / 2) >= 1.00,
    "RX2 clip overlaps the enlarged north antenna labels"
);

if (part == "base") {
    base();
} else if (part == "lid") {
    lid_print();
} else if (part == "insert_coupon") {
    insert_coupon();
} else if (part == "rx2_antenna_clip") {
    rx2_antenna_clip();
} else if (part == "rx2_clip_fit_coupon") {
    rx2_clip_fit_coupon();
} else if (part == "installed_case") {
    installed_case();
} else if (part == "interference") {
    interference_check();
} else if (part == "assembly") {
    assembly_view();
} else {
    assert(false, str("Unknown enclosure part selector: ", part));
}
