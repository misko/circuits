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
 *   openscad -o rx2_antenna_mount.stl \
 *       -D 'part="rx2_antenna_mount"' this_file.scad
 *   openscad -o rx2_antenna_fit_gauge.stl \
 *       -D 'part="rx2_antenna_fit_gauge"' this_file.scad
 */

part = "assembly";
explode = 10;            // assembly-view lid lift, mm
mount_explode = 8;       // additional mount lift above the exploded lid, mm
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

// Separate RX2/reference antenna mount.  The two additional inserts are the
// same E-Z LOK 260-M3-BR/CR cold-press family and the same coupon-qualified
// 4.25 mm production pilot as the four board fasteners above.
mount_points = [[-22.0, 8.0], [22.0, 8.0]];
mount_boss_drop = 3.50;
mount_boss_bottom_d = 9.00;
mount_boss_roof_d = 12.00;
mount_screw_seat_local_z = 2.70;
mount_screw_length = 8.00;       // M3 x 8 socket-head cap screw
mount_insert_bottom_z = inner_roof_z - mount_boss_drop;
mount_insert_top_z = mount_insert_bottom_z + insert_length;
mount_screw_bearing_z = overall_z + mount_screw_seat_local_z;
mount_screw_nonthread_z = mount_screw_bearing_z - mount_insert_top_z;
mount_screw_engagement = mount_screw_length - mount_screw_nonthread_z;
mount_screw_tip_clearance = insert_length - mount_screw_engagement;
mount_insert_roof_skin = overall_z - (
    mount_insert_bottom_z + insert_length + insert_bottom_clearance
);

// The mount is a closed-top hood in service and prints with that closed face
// on the bed.  Its one connected underside cavity receives the complete
// right-angle antenna; the lid closes that cavity after the two screws seat.
mount_size = [64.0, 37.0];
mount_center = [0.0, 5.5];
mount_radius = 3.0;
mount_wall = 3.0;
mount_roof = 3.0;
mount_candidate_body_d = 10.0;
mount_body_radial_clearance = 0.40;
// Conservative L-envelope derived from the supplied holder's perpendicular
// D9.75 paths: both lower branches remain D10.  Only the upper upright reduces
// to D8.75, after the holder-evidenced shoulder/taper interval.
mount_candidate_lower_upright_d = 10.0;
mount_candidate_upper_stalk_d = 8.75;
mount_stalk_radial_clearance = 0.40;
mount_body_axis_z = mount_candidate_body_d / 2 + 0.20;
mount_body_south_y = 0.0;
mount_stalk_y = 16.5;
mount_stalk_transition_start_z = 20.0;
mount_stalk_transition_end_z = 30.0;
mount_stalk_top_z = mount_body_axis_z + 34.0;
mount_h = mount_body_axis_z
        + mount_candidate_body_d / 2
        + mount_body_radial_clearance
        + mount_roof;
mount_locator_rail_bottom_z = 1.20;
mount_locator_rail_t = 2.00;
mount_locator_rail_y = [-2.0, 18.0];
mount_screw_column_d = 12.0;
mount_relief_size = [
    mount_size[0] - 2 * mount_wall,
    mount_size[1] - 2 * mount_wall
];

// User-supplied flexible-holder reference, measured from the exact bound STL.
// These are void/retention dimensions of a split, compliant grip—not rigid
// antenna dimensions and not production cavity sizes for this closed mount.
reference_holder_station_pitch = 23.75;
reference_holder_outer_clip_d = 19.75;
reference_holder_grip_bore_d = 9.75;
reference_holder_retention_lip_d = 8.75;
reference_holder_grip_radial_interference =
    (mount_candidate_body_d - reference_holder_grip_bore_d) / 2;
reference_holder_lip_radial_interference =
    (mount_candidate_body_d - reference_holder_retention_lip_d) / 2;

// Reference-only straight exterior cable.  The PCB lid remains completely
// closed beneath the mount.  The already-attached cable enters with the
// antenna through the large rectangular underside opening.  The bottom-open
// south-wall arch clears the complete D10 antenna body, not merely the cable,
// so the pre-wired assembly never needs to be threaded through a closed bore.
coax_candidate_d = 2.50;
coax_exit_radial_clearance =
    (mount_candidate_body_d + 2 * mount_body_radial_clearance
        - coax_candidate_d) / 2;
coax_exit_clearance_d =
    mount_candidate_body_d + 2 * mount_body_radial_clearance;
coax_exit_entry_flare_length = 1.00;
// The full-body arch already gives the cable 4.15 mm radial clearance.  Keep
// the entry at the same D10.8 profile so the hood retains 3.0 mm of roof.
coax_exit_entry_flare_d = coax_exit_clearance_d;
coax_exit_y = mount_center[1] - mount_size[1] / 2;
coax_tail_length = 45.0;
// Collision-only setback excludes the intended zero-thickness antenna/cable
// junction face.  The rendered reference remains tangent and continuous.
coax_collision_joint_setback = 0.05;
mount_insertion_travel = 45.0;

antenna_label_size = 4.20;
mount_fit_diameters = [9.0, 9.5, 10.0, 10.5];

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

module mount_outline_2d() {
    translate(mount_center)
        rounded_rect_2d(mount_size, mount_radius);
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

module lid_mount_bosses() {
    for (p = mount_points)
        translate([p[0], p[1], mount_insert_bottom_z])
            cylinder(
                h = mount_boss_drop + eps,
                d1 = mount_boss_bottom_d,
                d2 = mount_boss_roof_d
            );
}

module lid_mount_fastener_cuts() {
    pocket_depth = insert_length + insert_bottom_clearance;
    for (p = mount_points) {
        // Insert enters from the lid underside.  Its flange therefore reacts
        // an upward antenna pull into the boss rather than pulling out.
        translate([p[0], p[1], mount_insert_bottom_z - eps])
            cylinder(h = pocket_depth + 2 * eps, d = insert_hole_d);
        translate([p[0], p[1], mount_insert_bottom_z - eps])
            cylinder(
                h = insert_flange_recess_depth + eps,
                d = insert_flange_recess_d
            );
        translate([
            p[0], p[1],
            mount_insert_bottom_z + pocket_depth - eps
        ])
            cylinder(
                h = overall_z - mount_insert_bottom_z - pocket_depth + 2 * eps,
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
            lid_mount_bosses();
        }
        sma_cutouts();
        lid_lip_rabbet();
        service_opening();
        lid_fastener_cuts();
        lid_mount_fastener_cuts();
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

module mount_locator_rails() {
    // These two ribs hang from the roof and remain open below.  Their 10.8 mm
    // gap keys the D10 horizontal branch while allowing the complete L-shaped
    // antenna/cable assembly to translate vertically through the underside.
    body_cavity_d = mount_candidate_body_d
                  + 2 * mount_body_radial_clearance;
    rail_h = mount_h - mount_roof - mount_locator_rail_bottom_z;
    rail_y_len = mount_locator_rail_y[1] - mount_locator_rail_y[0];
    for (side = [-1, 1])
        translate([
            side * (body_cavity_d + mount_locator_rail_t) / 2,
            (mount_locator_rail_y[0] + mount_locator_rail_y[1]) / 2,
            mount_locator_rail_bottom_z
        ])
            linear_extrude(height = rail_h)
                rounded_rect_2d(
                    [mount_locator_rail_t, rail_y_len],
                    mount_locator_rail_t / 2
                );
}

module mount_upright_aperture() {
    stalk_cavity_d = mount_candidate_lower_upright_d
                   + 2 * mount_stalk_radial_clearance;
    // This is the only opening through the closed roof/top.
    translate([0, mount_stalk_y, -eps])
        cylinder(h = mount_h + 2 * eps, d = stalk_cavity_d);
}

module coax_exit_u_channel_cut() {
    inner_y = mount_center[1] - mount_size[1] / 2 + mount_wall + eps;
    cut_len = inner_y - coax_exit_y + 2 * eps;

    // Holder-STL-inspired open-bottom U-channel: two vertical sides rise to
    // the antenna/cable centerline and a semicircular roof clears the complete
    // D10 lower antenna branch with 0.40 mm radial clearance.  It opens
    // directly into the rectangular underside cavity, so the complete
    // attached assembly moves straight upward instead of being threaded.
    translate([
        -coax_exit_clearance_d / 2,
        coax_exit_y - eps,
        -eps
    ])
        cube([
            coax_exit_clearance_d,
            cut_len,
            mount_body_axis_z + 2 * eps
        ]);
    translate([0, coax_exit_y - eps, mount_body_axis_z])
        rotate([-90, 0, 0])
            cylinder(h = cut_len, d = coax_exit_clearance_d);

    // Preserve a one-millimetre entry transition at the exterior face.  The
    // full-body D10.8 arch needs no larger entry flare, which preserves
    // the audited 3.0 mm roof ligament.
    hull() {
        coax_u_channel_slice(
            coax_exit_y - eps,
            coax_exit_entry_flare_d,
            eps
        );
        coax_u_channel_slice(
            coax_exit_y + coax_exit_entry_flare_length,
            coax_exit_clearance_d,
            eps
        );
    }
}

module coax_u_channel_slice(y, diameter, thickness) {
    translate([-diameter / 2, y, -eps])
        cube([diameter, thickness, mount_body_axis_z + 2 * eps]);
    translate([0, y, mount_body_axis_z])
        rotate([-90, 0, 0])
            cylinder(h = thickness, d = diameter);
}

module mount_labels() {
    // Split the recessed south-wall label around the straight cable exit.
    for (row = [[-17.0, "RX2"], [15.0, "REFERENCE"]])
        translate([
            row[0],
            mount_center[1] - mount_size[1] / 2 + 0.45,
            7.4
        ])
            rotate([90, 0, 0])
                linear_extrude(height = 0.50)
                    text(
                        row[1],
                        size = 3.2,
                        halign = "center",
                        valign = "center",
                        font = "Liberation Sans:style=Bold"
                    );
}

module rx2_antenna_mount_installed() {
    difference() {
        union() {
            // Perimeter hood and closed roof.  Its relief, key walls, and
            // screw columns are all open from the underside in print/service.
            difference() {
                linear_extrude(height = mount_h)
                    mount_outline_2d();
                translate([mount_center[0], mount_center[1], -eps])
                    linear_extrude(height = mount_h - mount_roof + 2 * eps)
                        rounded_rect_2d(mount_relief_size, 1.5);
            }
            mount_locator_rails();
            for (p = mount_points)
                translate([p[0], p[1], 0])
                    cylinder(h = mount_h, d = mount_screw_column_d);
        }

        mount_upright_aperture();
        coax_exit_u_channel_cut();

        // Deep access wells retain the already-qualified M3x8 stack: the
        // screw head bears at local Z=2.70 mm while the closed roof stays high.
        for (p = mount_points) {
            translate([p[0], p[1], -eps])
                cylinder(
                    h = mount_screw_seat_local_z + 2 * eps,
                    d = screw_clearance_d
                );
            translate([p[0], p[1], mount_screw_seat_local_z])
                cylinder(
                    h = mount_h - mount_screw_seat_local_z + eps,
                    d = screw_head_d
                );
        }
        mount_labels();
    }
}

// Closed face on the bed; the entire underside cavity then grows upward and
// no trapped support is required inside the antenna pocket or screw wells.
module rx2_antenna_mount() {
    translate([0, 0, mount_h])
        rotate([180, 0, 0])
            rx2_antenna_mount_installed();
}

module fit_gauge_cell_cuts(body_d, center_x) {
    gauge_h = max(mount_fit_diameters) + 3.0;
    cavity_d = body_d + 2 * mount_body_radial_clearance;
    axis_z = body_d / 2 + 0.20;

    translate([center_x, -7.0 - eps, axis_z])
        rotate([-90, 0, 0])
            cylinder(h = 9.8, d = cavity_d);
    translate([
        center_x - cavity_d / 2 - 0.80,
        -7.0 - eps,
        -eps
    ])
        cube([
            cavity_d + 1.60,
            10.0,
            axis_z + 1.20 + eps
        ]);
    translate([center_x, 2.0, axis_z - eps])
        cylinder(
            h = gauge_h - axis_z + 2 * eps,
            d = mount_candidate_lower_upright_d
              + 2 * mount_stalk_radial_clearance
        );
}

module rx2_antenna_fit_gauge_installed() {
    gauge_h = max(mount_fit_diameters) + 3.0;
    gauge_x = [-28.5, -9.5, 9.5, 28.5];
    cell_size = [15.5, 16.0];

    difference() {
        union() {
            for (x = gauge_x)
                translate([x, 1.0, 0])
                    linear_extrude(height = gauge_h)
                        rounded_rect_2d(cell_size, 2.0);
            // North spine makes the four stations one deterministic part.
            translate([0, 8.0, 0])
                linear_extrude(height = gauge_h)
                    rounded_rect_2d([74.0, 2.0], 0.8);
        }
        for (i = [0 : len(mount_fit_diameters) - 1])
            fit_gauge_cell_cuts(mount_fit_diameters[i], gauge_x[i]);
    }
}

module rx2_antenna_fit_gauge() {
    gauge_h = max(mount_fit_diameters) + 3.0;
    gauge_x = [-28.5, -9.5, 9.5, 28.5];
    difference() {
        translate([0, 0, gauge_h])
            rotate([180, 0, 0])
                rx2_antenna_fit_gauge_installed();
        // Values face outward on the vertical spine in the exported print
        // orientation; unlike top-face labels, they do not touch the bed.
        for (i = [0 : len(mount_fit_diameters) - 1])
            translate([gauge_x[i], -8.55, gauge_h / 2])
                rotate([90, 0, 0])
                    linear_extrude(height = 0.50)
                        text(
                            str(mount_fit_diameters[i]),
                            size = 2.8,
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
    antenna_axis_z = mount_body_axis_z;

    color([0.92, 0.43, 0.12])
        rx2_reference_antenna_solid();

    coax_reference_route();
}

// Separate non-printable candidate antenna artifact.  The nominal D10 body
// is retained independently of the supplied split-holder STL: that STL proves
// a D9.75 compliant grip region and D8.75 retention lip, not antenna OD.  The
// remaining body length/taper dimensions are still candidate envelopes.
module antenna_horizontal_body_solid() {
    antenna_axis_z = mount_body_axis_z;
    translate([0, mount_body_south_y, antenna_axis_z])
        rotate([-90, 0, 0])
            cylinder(
                h = mount_stalk_y - mount_body_south_y,
                d = mount_candidate_body_d
            );
}

module antenna_lower_upright_solid() {
    antenna_axis_z = mount_body_axis_z;
    translate([0, mount_stalk_y, antenna_axis_z])
        cylinder(
            h = mount_stalk_transition_start_z - antenna_axis_z,
            d = mount_candidate_lower_upright_d
        );
}

module antenna_transition_solid() {
    translate([0, mount_stalk_y, mount_stalk_transition_start_z])
        cylinder(
            h = mount_stalk_transition_end_z
                - mount_stalk_transition_start_z,
            d1 = mount_candidate_lower_upright_d,
            d2 = mount_candidate_upper_stalk_d
        );
}

module antenna_upper_upright_solid() {
    translate([0, mount_stalk_y, mount_stalk_transition_end_z])
        cylinder(
            h = mount_stalk_top_z - mount_stalk_transition_end_z,
            d = mount_candidate_upper_stalk_d
        );
}

module rx2_reference_antenna_solid() {
    union() {
        antenna_horizontal_body_solid();
        // The perpendicular lower upright is also D10.  It steps down only
        // after the measured holder's z20..30 taper region; the rigid mount
        // aperture clears D10 rather than relying on flex/interference.
        antenna_lower_upright_solid();
        antenna_transition_solid();
        antenna_upper_upright_solid();

    }
}

module coax_reference_route() {
    // One straight exterior leg continues south from the horizontal D10 body.
    // It never crosses the PCB lid and has no hidden bend or S-shaped route.
    color([0.20, 0.20, 0.22])
        translate([0, mount_body_south_y, mount_body_axis_z])
            rotate([90, 0, 0])
                cylinder(h = coax_tail_length, d = coax_candidate_d);
}

module coax_reference_route_collision_solid() {
    // CGAL otherwise exports the intended coincident junction face as a
    // non-manifold pseudo-solid.  Set back only the collision witness by one
    // modeling epsilon; this does not alter the rendered cable route.
    translate([
        0,
        mount_body_south_y - coax_collision_joint_setback,
        mount_body_axis_z
    ])
        rotate([90, 0, 0])
            cylinder(
                h = coax_tail_length - coax_collision_joint_setback,
                d = coax_candidate_d
            );
}

module swept_z(travel) {
    hull() {
        children();
        translate([0, 0, -travel]) children();
    }
}

module rx2_reference_insertion_sweep_solid() {
    // Exact convex-primitives sweep for one straight vertical insertion.
    // Sweeping each primitive separately avoids the false convex fill that a
    // hull around the complete non-convex L assembly would introduce.
    union() {
        swept_z(mount_insertion_travel) antenna_horizontal_body_solid();
        swept_z(mount_insertion_travel) antenna_lower_upright_solid();
        swept_z(mount_insertion_travel) antenna_transition_solid();
        swept_z(mount_insertion_travel) antenna_upper_upright_solid();
        // Sweep the complete pre-wired cable, including its tangent junction
        // face.  The 0.05 mm setback belongs only to the antenna-vs-cable
        // self-intersection witness and must not create a loading-path gap.
        swept_z(mount_insertion_travel) coax_reference_route();
    }
}

module mount_insert_references(lid_shift = 0) {
    color([0.76, 0.52, 0.16])
        for (p = mount_points) {
            translate([
                p[0], p[1],
                mount_insert_bottom_z + lid_shift
            ])
                cylinder(h = insert_length, d = 4.216);
            translate([
                p[0], p[1],
                mount_insert_bottom_z + lid_shift
            ])
                cylinder(h = insert_flange_recess_depth, d = 5.537);
        }
}

module mount_screw_references(mount_shift = 0) {
    color([0.50, 0.53, 0.56])
        for (p = mount_points) {
            translate([
                p[0], p[1],
                mount_screw_bearing_z - mount_screw_length + mount_shift
            ])
                cylinder(h = mount_screw_length, d = 3.0);
            translate([
                p[0], p[1],
                mount_screw_bearing_z + mount_shift
            ])
                cylinder(h = 3.0, d = 5.5);
        }
}

module rx2_reference_antenna_installed() {
    translate([0, 0, overall_z])
        rx2_reference_antenna_solid();
}

module coax_reference_route_installed() {
    translate([0, 0, overall_z])
        coax_reference_route();
}

module mount_lid_plastic_installed() {
    union() {
        lid_final();
        translate([0, 0, overall_z - eps])
            rx2_antenna_mount_installed();
    }
}

module mount_fastener_references_installed() {
    union() {
        mount_insert_references();
        mount_screw_references();
    }
}

module antenna_vs_mount_lid_interference() {
    intersection() {
        rx2_reference_antenna_installed();
        mount_lid_plastic_installed();
    }
}

module antenna_vs_fasteners_interference() {
    intersection() {
        rx2_reference_antenna_installed();
        mount_fastener_references_installed();
    }
}

module antenna_vs_board_interference() {
    intersection() {
        rx2_reference_antenna_installed();
        union() {
            board_reference_interior();
            component_references();
        }
    }
}

module antenna_vs_cable_interference() {
    intersection() {
        rx2_reference_antenna_installed();
        translate([0, 0, overall_z])
            coax_reference_route_collision_solid();
    }
}

module cable_vs_mount_lid_interference() {
    intersection() {
        coax_reference_route_installed();
        mount_lid_plastic_installed();
    }
}

module insertion_sweep_vs_mount_interference() {
    intersection() {
        rx2_reference_insertion_sweep_solid();
        rx2_antenna_mount_installed();
    }
}

module rx2_reference_interference() {
    union() {
        antenna_vs_mount_lid_interference();
        antenna_vs_fasteners_interference();
        antenna_vs_board_interference();
        antenna_vs_cable_interference();
        cable_vs_mount_lid_interference();
        insertion_sweep_vs_mount_interference();
    }
}

module upward_insertion_arrow() {
    color([0.18, 0.66, 0.30]) {
        translate([-14.0, 6.0, -24.0])
            cylinder(h = 12.0, d = 1.8);
        translate([-14.0, 6.0, -12.0])
            cylinder(h = 4.0, d1 = 5.0, d2 = 0.0);
    }
}

// Exploded underside-loading evidence.  The complete already-wired assembly
// is displaced downward on the same straight path used by the sweep proof.
// It enters the one rectangular underside opening without cable threading.
module antenna_mount_insertion_view(insertion_offset = -45.0) {
    // Slight transparency is evidence-view-only and exposes the uninterrupted
    // rectangular entry plus roof-hung rails behind the incoming assembly.
    color([0.25, 0.52, 0.72, 0.62])
        rx2_antenna_mount_installed();
    color([0.92, 0.43, 0.12])
        translate([0, 0, insertion_offset])
            rx2_reference_antenna_solid();
    color([0.16, 0.16, 0.18])
        translate([0, 0, insertion_offset])
            coax_reference_route();
    // Translucent final-position witness makes the common straight Z axis
    // explicit without hiding the fully-below start state.
    color([0.92, 0.43, 0.12, 0.20])
        rx2_reference_antenna_solid();
    color([0.16, 0.16, 0.18, 0.20])
        coax_reference_route();
    color([0.58, 0.60, 0.63])
        translate([0, 0, -overall_z])
            mount_screw_references();
    upward_insertion_arrow();
}

// Underside loading view analogous to the supplied visual reference: the
// mount remains closed on top, its single lower opening faces the camera, and
// the separate candidate antenna is orange inside the blue authored cavity.
module antenna_mount_cutaway_view() {
    color([0.25, 0.52, 0.72, 0.52])
        rx2_antenna_mount_installed();
    color([0.92, 0.43, 0.12])
        rx2_reference_antenna_solid();
    color([0.18, 0.18, 0.20])
        coax_reference_route();
    color([0.52, 0.55, 0.58])
        translate([0, 0, -overall_z])
            mount_screw_references();
}

module mount_lid_patch_local() {
    intersection() {
        translate([0, 0, -overall_z])
            lid_final();
        translate([
            mount_center[0] - mount_size[0] / 2,
            mount_center[1] - mount_size[1] / 2,
            -roof - eps
        ])
            cube([mount_size[0], mount_size[1], roof + 2 * eps]);
    }
}

// Longitudinal center section removes a 12 mm-wide plastic strip while
// retaining both D12 screw columns.  It exposes the complete orange D10 lower
// L, its D10->D8.75 upright transition, the blue rigid cavity/closed lid,
// both gray fastener stacks, and the dark straight exterior cable in one view.
module antenna_mount_section_view() {
    section_w = 12.0;
    color([0.25, 0.52, 0.72])
        difference() {
            union() {
                rx2_antenna_mount_installed();
                mount_lid_patch_local();
            }
            translate([
                -section_w / 2,
                mount_center[1] - mount_size[1] / 2 - 1.0,
                -roof - 1.0
            ])
                cube([
                    section_w,
                    mount_size[1] + 2.0,
                    mount_stalk_top_z + roof + 2.0
                ]);
        }
    color([0.92, 0.43, 0.12])
        rx2_reference_antenna_solid();
    color([0.16, 0.16, 0.18])
        coax_reference_route();
    color([0.58, 0.60, 0.63]) {
        translate([0, 0, -overall_z])
            mount_screw_references();
        translate([0, 0, -overall_z])
            mount_insert_references();
    }
}

// True Y/Z half-section for a profile view.  Keeping x>=0 exposes the antenna
// center plane without changing the authored production mesh.
module antenna_mount_profile_section_view() {
    color([0.25, 0.52, 0.72])
        intersection() {
            union() {
                rx2_antenna_mount_installed();
                mount_lid_patch_local();
            }
            translate([
                0,
                mount_center[1] - mount_size[1] / 2 - 1.0,
                -roof - 1.0
            ])
                cube([
                    mount_size[0] / 2 + 1.0,
                    mount_size[1] + 2.0,
                    mount_stalk_top_z + roof + 2.0
                ]);
        }
    color([0.92, 0.43, 0.12])
        rx2_reference_antenna_solid();
    color([0.16, 0.16, 0.18])
        coax_reference_route();
    color([0.58, 0.60, 0.63]) {
        translate([0, 0, -overall_z])
            mount_screw_references();
        translate([0, 0, -overall_z])
            mount_insert_references();
    }
}

// Evidence-only cutaway retains the left-side shell/column beyond x=-7 mm,
// leaving the complete centerline L antenna, roof-hung rail gap, U-notch, and
// closed-lid floor unobscured.  Production geometry is unchanged.
module antenna_mount_clearance_cutaway_view() {
    color([0.25, 0.52, 0.72]) {
        intersection() {
            rx2_antenna_mount_installed();
            translate([
                -mount_size[0] / 2 - 1.0,
                mount_center[1] - mount_size[1] / 2 - 1.0,
                -1.0
            ])
                cube([
                    mount_size[0] / 2 - 6.0,
                    mount_size[1] + 2.0,
                    mount_stalk_top_z + 2.0
                ]);
        }
        mount_lid_patch_local();
    }
    color([0.92, 0.43, 0.12])
        rx2_reference_antenna_solid();
    color([0.16, 0.16, 0.18])
        coax_reference_route();
    color([0.58, 0.60, 0.63]) {
        translate([0, 0, -overall_z])
            mount_screw_references();
        translate([0, 0, -overall_z])
            mount_insert_references();
    }
}

module center_x_slice(half_thickness = 0.35) {
    intersection() {
        children();
        translate([-half_thickness, -60.0, -5.0])
            cube([2 * half_thickness, 120.0, 60.0]);
    }
}

// Exact longitudinal Y/Z center section, rotated face-on for an unambiguous
// evidence render.  It visibly binds the closed lid floor, orange horizontal
// body below the roof, upright through-aperture, and black cable seated in the
// bottom-open south U-channel.  This selector never enters printable-parts.
module antenna_mount_longitudinal_section_view() {
    color([0.25, 0.52, 0.72])
        antenna_mount_longitudinal_section_plastic();
    color([0.92, 0.43, 0.12])
        antenna_mount_longitudinal_section_antenna();
    color([0.16, 0.16, 0.18])
        antenna_mount_longitudinal_section_cable();
}

module antenna_mount_longitudinal_section_plastic() {
    rotate([0, 90, 0])
        center_x_slice()
            union() {
                rx2_antenna_mount_installed();
                mount_lid_patch_local();
            }
}

module antenna_mount_longitudinal_section_antenna() {
    rotate([0, 90, 0])
        center_x_slice()
            rx2_reference_antenna_solid();
}

module antenna_mount_longitudinal_section_cable() {
    rotate([0, 90, 0])
        center_x_slice()
            coax_reference_route();
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
        translate([0, 0, overall_z + explode + mount_explode])
            rx2_antenna_mount_installed();
    if (show_reference_antenna)
        translate([0, 0, overall_z + explode + mount_explode])
            rx2_reference_antenna();
    if (show_fastener_references) {
        mount_insert_references(explode);
        mount_screw_references(explode + mount_explode);
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
            rx2_antenna_mount_installed();
    }
}

// A successful clearance test exports no geometry. Contact at the four
// plastic support annuli is intentionally zero-thickness and therefore does
// not appear as a solid intersection.
module interference_check() {
    union() {
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

        // Candidate antenna, cable, mount/lid, fasteners, and simplified-board
        // witnesses must have no volumetric overlap.  The rendered antenna
        // and cable are tangent at one intended zero-volume interface; the
        // collision-only cable witness excludes that face by one epsilon so
        // CGAL cannot emit it as a non-manifold pseudo-solid.  Exact
        // STEP/component checks remain separate bound evidence.
        rx2_reference_interference();
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
assert((mount_boss_bottom_d - insert_flange_recess_d) / 2 >= 0.90,
       "RX2 mount insert boss violates 0.90 mm minimum radial wall");
assert(mount_insert_roof_skin >= 0.80,
       "RX2 mount insert pocket leaves less than 0.80 mm roof skin");
assert(mount_screw_engagement >= 4.00,
       "M3x8 RX2 mount screw has less than 4.00 mm insert engagement");
assert(mount_screw_tip_clearance >= 0.20,
       "M3x8 RX2 mount screw would bottom in the insert");
assert((mount_screw_column_d - screw_head_d) / 2 >= 2.40,
       "RX2 mount screw well has less than 2.40 mm radial wall");
assert(mount_roof >= 3.00,
       "RX2 mount closed roof is thinner than 3.00 mm");
assert(mount_body_radial_clearance >= 0.40,
       "RX2 rigid closed pocket has less than 0.40 mm radial clearance");
assert(abs(reference_holder_grip_radial_interference - 0.125) <= 0.001,
       "Bound split-holder D9.75 grip interpretation drifted from D10 body");
assert(abs(reference_holder_lip_radial_interference - 0.625) <= 0.001,
       "Bound split-holder D8.75 lip interpretation drifted from D10 body");
assert(reference_holder_outer_clip_d > mount_candidate_body_d,
       "Bound split-holder outer clip no longer surrounds the D10 witness");
assert(
    mount_locator_rail_t >= 2.00,
    "RX2 roof-hung locator rail is thinner than 2.00 mm"
);
assert(
    mount_locator_rail_bottom_z >= 1.00
        && mount_locator_rail_bottom_z < mount_body_axis_z,
    "RX2 locator rails no longer hang above the underside entry"
);
assert(
    mount_body_axis_z - mount_candidate_body_d / 2 >= 0.15
        && mount_body_axis_z - mount_candidate_body_d / 2 <= 0.60,
    "RX2 body-to-lid closure gap leaves the captive range"
);
assert(
    mount_center[1] + mount_size[1] / 2
        - (mount_stalk_y
            + (mount_candidate_lower_upright_d
                + 2 * mount_stalk_radial_clearance) / 2) >= 1.80,
    "RX2 keyed stalk aperture has less than 1.80 mm north wall"
);
assert((coax_exit_clearance_d - mount_candidate_body_d) / 2
        >= mount_body_radial_clearance,
       "South U-arch no longer clears the full antenna body radius");
assert(coax_exit_radial_clearance >= 1.00,
       "Straight exterior cable exit has less than 1.00 mm radial clearance");
assert(coax_collision_joint_setback > 0
        && coax_collision_joint_setback <= eps,
       "Cable collision witness setback must be positive and <= one epsilon");
assert(coax_tail_length > coax_collision_joint_setback,
       "Cable collision witness setback consumes the exterior tail");
assert(coax_exit_entry_flare_length >= 1.00,
       "Open-bottom pre-wired assembly U-arch entry is shorter than 1.00 mm");
assert(coax_exit_entry_flare_d >= coax_exit_clearance_d,
       "South U-arch entry is smaller than its full-body core");
assert(mount_h - (mount_body_axis_z + coax_exit_entry_flare_d / 2)
        >= mount_roof - eps,
       "Open-bottom pre-wired assembly U-arch leaves less than 3.00 mm roof ligament");
assert(mount_body_axis_z - coax_candidate_d / 2 >= 3.50,
       "Straight exterior cable is too close to the closed PCB lid");
assert(coax_exit_y - (service_center[1] + service_size[1] / 2) >= 4.00,
       "Open-bottom full-antenna U-arch crowds the SWD/5V service opening");
assert(mount_relief_size == [58.0, 31.0],
       "RX2 underside loading relief drifted from the audited 58 x 31 mm rectangle");
assert(
    mount_center[1] + mount_relief_size[1] / 2 == 21.0
        && mount_stalk_y
            + (mount_candidate_lower_upright_d
                + 2 * mount_stalk_radial_clearance) / 2 == 21.9,
    "RX2 upright footprint/rectangular relief union drifted from audited extents"
);
assert(mount_insertion_travel >= mount_stalk_top_z + 5.00,
       "Insertion sweep does not begin with the upright below the adapter");
assert(
    (mount_center[1] - mount_size[1] / 2)
        - (service_center[1] + service_size[1] / 2) >= 4.00,
    "RX2 mount leaves less than 4.00 mm to the removable-lid service opening"
);
assert(
    27.2 - antenna_label_size / 2
        - (mount_center[1] + mount_size[1] / 2) >= 1.00,
    "RX2 mount overlaps the enlarged north antenna labels"
);

echo(str("PCB_ENCLOSURE_SELECTOR:", part));
echo(str(
    "PCB_ENCLOSURE_FACTS:",
    "board_bottom_z=", pcb_bottom_z,
    ";case_top_z=", overall_z,
    ";mount_h=", mount_h,
    ";mount_roof=", mount_roof,
    ";mount_wall=", mount_wall,
    ";mount_half_x=", mount_size[0] / 2,
    ";mount_center_y=", mount_center[1],
    ";body_d=", mount_candidate_body_d,
    ";lower_upright_d=", mount_candidate_lower_upright_d,
    ";upper_upright_d=", mount_candidate_upper_stalk_d,
    ";body_axis_z=", mount_body_axis_z,
    ";body_south_y=", mount_body_south_y,
    ";stalk_y=", mount_stalk_y,
    ";transition_start_z=", mount_stalk_transition_start_z,
    ";transition_end_z=", mount_stalk_transition_end_z,
    ";stalk_top_z=", mount_stalk_top_z,
    ";body_radial_clearance=", mount_body_radial_clearance,
    ";stalk_radial_clearance=", mount_stalk_radial_clearance,
    ";relief_x=", mount_relief_size[0],
    ";relief_y=", mount_relief_size[1],
    ";rail_gap=", mount_candidate_body_d + 2 * mount_body_radial_clearance,
    ";rail_t=", mount_locator_rail_t,
    ";cable_d=", coax_candidate_d,
    ";cable_core_d=", coax_exit_clearance_d,
    ";flare_length=", coax_exit_entry_flare_length,
    ";flare_d=", coax_exit_entry_flare_d,
    ";insertion_sweep=", mount_insertion_travel,
    ";cable_tail_length=", coax_tail_length,
    ";mount_south_y=", mount_center[1] - mount_size[1] / 2,
    ";mount_north_y=", mount_center[1] + mount_size[1] / 2,
    ";service_right_x=", service_center[0] + service_size[0] / 2,
    ";service_north_y=", service_center[1] + service_size[1] / 2,
    ";north_label_y=27.2",
    ";antenna_label_size=", antenna_label_size,
    ";outer_half_y=", outer_size[1] / 2
));

selector_known =
       part == "base"
    || part == "lid"
    || part == "insert_coupon"
    || part == "rx2_antenna_mount"
    || part == "rx2_antenna_fit_gauge"
    || part == "rx2_antenna_reference"
    || part == "rx2_cable_reference"
    || part == "installed_case"
    || part == "interference"
    || part == "antenna_vs_mount_lid"
    || part == "antenna_vs_fasteners"
    || part == "antenna_vs_board"
    || part == "antenna_vs_cable"
    || part == "cable_vs_mount_lid"
    || part == "insertion_sweep_vs_mount"
    || part == "antenna_mount_cutaway"
    || part == "antenna_mount_insertion"
    || part == "antenna_mount_insertion_entry"
    || part == "antenna_mount_section"
    || part == "antenna_mount_profile_section"
    || part == "antenna_mount_clearance_cutaway"
    || part == "antenna_mount_longitudinal_section"
    || part == "antenna_mount_longitudinal_section_plastic"
    || part == "antenna_mount_longitudinal_section_antenna"
    || part == "antenna_mount_longitudinal_section_cable"
    || part == "assembly";
assert(selector_known, str("Unknown enclosure part selector: ", part));
echo(str("PCB_ENCLOSURE_SELECTOR_OK:", part));

if (part == "base") {
    base();
} else if (part == "lid") {
    lid_print();
} else if (part == "insert_coupon") {
    insert_coupon();
} else if (part == "rx2_antenna_mount") {
    rx2_antenna_mount();
} else if (part == "rx2_antenna_fit_gauge") {
    rx2_antenna_fit_gauge();
} else if (part == "rx2_antenna_reference") {
    rx2_reference_antenna_solid();
} else if (part == "rx2_cable_reference") {
    coax_reference_route();
} else if (part == "installed_case") {
    installed_case();
} else if (part == "interference") {
    interference_check();
} else if (part == "antenna_vs_mount_lid") {
    antenna_vs_mount_lid_interference();
} else if (part == "antenna_vs_fasteners") {
    antenna_vs_fasteners_interference();
} else if (part == "antenna_vs_board") {
    antenna_vs_board_interference();
} else if (part == "antenna_vs_cable") {
    antenna_vs_cable_interference();
} else if (part == "cable_vs_mount_lid") {
    cable_vs_mount_lid_interference();
} else if (part == "insertion_sweep_vs_mount") {
    insertion_sweep_vs_mount_interference();
} else if (part == "antenna_mount_cutaway") {
    antenna_mount_cutaway_view();
} else if (part == "antenna_mount_insertion") {
    antenna_mount_insertion_view();
} else if (part == "antenna_mount_insertion_entry") {
    antenna_mount_insertion_view(-18.0);
} else if (part == "antenna_mount_section") {
    antenna_mount_section_view();
} else if (part == "antenna_mount_profile_section") {
    antenna_mount_profile_section_view();
} else if (part == "antenna_mount_clearance_cutaway") {
    antenna_mount_clearance_cutaway_view();
} else if (part == "antenna_mount_longitudinal_section") {
    antenna_mount_longitudinal_section_view();
} else if (part == "antenna_mount_longitudinal_section_plastic") {
    antenna_mount_longitudinal_section_plastic();
} else if (part == "antenna_mount_longitudinal_section_antenna") {
    antenna_mount_longitudinal_section_antenna();
} else if (part == "antenna_mount_longitudinal_section_cable") {
    antenna_mount_longitudinal_section_cable();
} else if (part == "assembly") {
    assembly_view();
} else {
    assert(false, str("Unknown enclosure part selector: ", part));
}
