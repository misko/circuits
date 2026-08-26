/*
 * pcb-enclosure rectangular engine v1
 *
 * Variables are prepended by generate_enclosure.py. The engine deliberately
 * contains no board-specific dimensions or connector identities.
 */

$fn = 48;
eps = 0.05;

inner_size = [
    board_size[0] + 2 * xy_clearance,
    board_size[1] + 2 * xy_clearance
];
outer_size = [inner_size[0] + 2 * wall, inner_size[1] + 2 * wall];
overall_z = inside_top_z + roof;
pcb_top_z = board_bottom_z + board_thickness;

assert(fastener_strategy == "shared_board" ||
       fastener_strategy == "separate_perimeter",
       str("Unknown fastener strategy: ", fastener_strategy));

module rounded_rect_2d(size, radius) {
    rr = min(radius, min(size[0], size[1]) / 2 - 0.01);
    offset(r = rr)
        square([size[0] - 2 * rr, size[1] - 2 * rr], center = true);
}

module shell_2d() {
    difference() {
        rounded_rect_2d(outer_size, corner_radius);
        rounded_rect_2d(inner_size, max(0.2, corner_radius - wall));
    }
}

module access_profile_2d(w, h, shape) {
    if (shape == "round") {
        circle(d = min(w, h));
    } else if (shape == "arch") {
        flat = min(w / 3, 4.0);
        slope = min((w - flat) / 2, h / 2);
        polygon([
            [-w/2, -h/2], [w/2, -h/2],
            [w/2, h/2 - slope], [flat/2, h/2],
            [-flat/2, h/2], [-w/2, h/2 - slope]
        ]);
    } else {
        square([w, h], center = true);
    }
}

module side_access_cut(port) {
    // port = [id, ref, side, disposition, x, y, z, shape, w, h]
    side = port[2]; x = port[4]; y = port[5]; z = port[6];
    shape = port[7]; w = port[8]; h = port[9];
    dx = outer_size[0] / 2 - board_size[0] / 2 + 2;
    dy = outer_size[1] / 2 - board_size[1] / 2 + 2;
    if (side == "north")
        multmatrix([[1,0,0,x], [0,0,1,board_size[1]/2-1],
                    [0,1,0,z], [0,0,0,1]])
            linear_extrude(height = dy)
                access_profile_2d(w, h, shape);
    if (side == "south")
        multmatrix([[1,0,0,x], [0,0,-1,-board_size[1]/2+1],
                    [0,1,0,z], [0,0,0,1]])
            linear_extrude(height = dy)
                access_profile_2d(w, h, shape);
    if (side == "east")
        multmatrix([[0,0,1,board_size[0]/2-1], [1,0,0,y],
                    [0,1,0,z], [0,0,0,1]])
            linear_extrude(height = dx)
                access_profile_2d(w, h, shape);
    if (side == "west")
        multmatrix([[0,0,-1,-board_size[0]/2+1], [1,0,0,y],
                    [0,1,0,z], [0,0,0,1]])
            linear_extrude(height = dx)
                access_profile_2d(w, h, shape);
}

module all_side_access_cuts() {
    for (port = ports)
        if ((port[3] == "opening" || port[3] == "service_opening") &&
            port[2] != "top")
            side_access_cut(port);
}

module top_access_cuts() {
    for (port = ports)
        if (port[3] == "service_opening" && port[2] == "top")
            translate([port[4], port[5], inside_top_z - eps])
                linear_extrude(height = roof + 2 * eps)
                    access_profile_2d(port[8], port[9], port[7]);
    for (vent = vents) {
        cx = vent[0]; cy = vent[1]; count = vent[2];
        length = vent[3]; width = vent[4]; pitch = vent[5]; axis = vent[6];
        for (i = [0:count-1]) {
            offset = (i - (count - 1) / 2) * pitch;
            translate([
                cx + (axis == "y" ? offset : 0),
                cy + (axis == "x" ? offset : 0),
                inside_top_z - eps
            ])
                linear_extrude(height = roof + 2 * eps)
                    rounded_rect_2d(
                        axis == "x" ? [length, width] : [width, length],
                        width / 2
                    );
        }
    }
}

module boss_set(points, diameter, top_z) {
    for (p = points)
        translate([p[0], p[1], floor - eps])
            cylinder(h = top_z - floor + eps, d = diameter);
}

module insert_pocket_set(points, top_z) {
    depth = insert_length + insert_bottom_clearance;
    for (p = points) {
        translate([p[0], p[1], top_z - depth])
            cylinder(h = depth + eps, d = insert_hole_d);
        translate([p[0], p[1], top_z - insert_flange_recess_depth])
            cylinder(h = insert_flange_recess_depth + eps,
                     d = insert_flange_recess_d);
    }
}

module base_lip() {
    overlap = 0.20;
    translate([0, 0, seam_z - eps])
        linear_extrude(height = lip_h + eps)
            difference() {
                rounded_rect_2d(
                    [inner_size[0] + 2*overlap, inner_size[1] + 2*overlap],
                    max(0.2, corner_radius - wall + overlap));
                rounded_rect_2d(
                    [inner_size[0] - 2*lip_t, inner_size[1] - 2*lip_t],
                    max(0.2, corner_radius - wall - lip_t));
            }
}

module lid_rabbet() {
    overlap = 0.20;
    translate([0, 0, seam_z - eps])
        linear_extrude(height = lip_h + 2*eps)
            difference() {
                rounded_rect_2d([
                    inner_size[0] + 2*(overlap + lip_clearance),
                    inner_size[1] + 2*(overlap + lip_clearance)
                ], max(0.2, corner_radius - wall + overlap + lip_clearance));
                rounded_rect_2d([
                    inner_size[0] - 2*(lip_t + 1.0),
                    inner_size[1] - 2*(lip_t + 1.0)
                ], max(0.2, corner_radius - wall - lip_t - 1.0));
            }
}

module split_base() {
    difference() {
        union() {
            linear_extrude(height = floor)
                rounded_rect_2d(outer_size, corner_radius);
            translate([0, 0, floor - eps])
                linear_extrude(height = seam_z - floor + eps)
                    shell_2d();
            boss_set(board_mount_holes, boss_d, board_bottom_z);
            if (fastener_strategy == "separate_perimeter")
                boss_set(case_holes, case_post_d, inside_top_z);
            base_lip();
        }
        all_side_access_cuts();
        insert_pocket_set(board_mount_holes, board_bottom_z);
        if (fastener_strategy == "separate_perimeter")
            insert_pocket_set(case_holes, inside_top_z);
    }
}

module lid_fastener_cuts(points, bearing_z) {
    for (p = points) {
        translate([p[0], p[1], seam_z - eps])
            cylinder(h = overall_z - seam_z + 2*eps, d = screw_clearance_d);
        translate([p[0], p[1], bearing_z])
            cylinder(h = overall_z - bearing_z + eps, d = screw_head_d);
    }
}

module split_lid_assembled() {
    bearing_z = overall_z - screw_head_recess_depth;
    closure_holes = fastener_strategy == "shared_board"
        ? board_mount_holes : case_holes;
    difference() {
        union() {
            translate([0, 0, seam_z - eps])
                linear_extrude(height = inside_top_z - seam_z + eps)
                    shell_2d();
            translate([0, 0, inside_top_z - eps])
                linear_extrude(height = roof + eps)
                    rounded_rect_2d(outer_size, corner_radius);
            if (fastener_strategy == "shared_board")
                for (p = board_mount_holes)
                    translate([p[0], p[1], pcb_top_z + lid_column_board_gap])
                        cylinder(h = inside_top_z - pcb_top_z - lid_column_board_gap + eps,
                                 d = lid_column_d);
        }
        all_side_access_cuts();
        top_access_cuts();
        lid_rabbet();
        lid_fastener_cuts(closure_holes, bearing_z);
    }
}

module panel_base() {
    difference() {
        union() {
            linear_extrude(height = floor)
                rounded_rect_2d(outer_size, corner_radius);
            translate([0, 0, floor - eps])
                linear_extrude(height = panel_capture + eps)
                    shell_2d();
            boss_set(board_mount_holes, boss_d, board_bottom_z);
            boss_set(case_holes, case_post_d, inside_top_z);
        }
        insert_pocket_set(board_mount_holes, board_bottom_z);
        insert_pocket_set(case_holes, inside_top_z);
    }
}

module panel_lid_assembled() {
    bearing_z = overall_z - screw_head_recess_depth;
    difference() {
        union() {
            translate([0, 0, inside_top_z - eps])
                linear_extrude(height = roof + eps)
                    rounded_rect_2d(outer_size, corner_radius);
            translate([0, 0, inside_top_z - panel_capture])
                linear_extrude(height = panel_capture + eps)
                    shell_2d();
        }
        top_access_cuts();
        lid_fastener_cuts(case_holes, bearing_z);
    }
}

function panel_span(side) =
    (side == "north" || side == "south" ? inner_size[0] : inner_size[1])
    - 2*corner_post_d - 2*panel_clearance;

function port_u(port, side) =
    (side == "north" || side == "south") ? port[4] : port[5];

module flat_panel(side) {
    span = panel_span(side);
    height = inside_top_z - floor;
    linear_extrude(height = panel_thickness)
        difference() {
            square([span, height], center = true);
            for (port = ports)
                if ((port[3] == "opening" || port[3] == "service_opening") &&
                    port[2] == side)
                    translate([port_u(port, side), port[6] - (floor + height/2)])
                        access_profile_2d(port[8], port[9], port[7]);
        }
}

module assembled_panel(side) {
    span = panel_span(side);
    height = inside_top_z - floor;
    if (side == "north")
        translate([0, outer_size[1]/2, floor + height/2])
            rotate([90, 0, 0]) flat_panel(side);
    if (side == "south")
        translate([0, -outer_size[1]/2, floor + height/2])
            rotate([-90, 0, 0]) flat_panel(side);
    if (side == "east")
        translate([outer_size[0]/2, 0, floor + height/2])
            multmatrix([[0,0,-1,0], [1,0,0,0], [0,1,0,0], [0,0,0,1]])
                flat_panel(side);
    if (side == "west")
        translate([-outer_size[0]/2, 0, floor + height/2])
            multmatrix([[0,0,1,0], [1,0,0,0], [0,1,0,0], [0,0,0,1]])
                flat_panel(side);
}

module insert_coupon() {
    sizes = [insert_hole_d - 0.10, insert_hole_d,
             insert_hole_d + 0.10, insert_hole_d + 0.20];
    difference() {
        union() {
            translate([-26, -9, 0]) cube([52, 18, 6]);
            for (i = [0:3])
                translate([(i - 1.5)*12, 0, 6-eps])
                    cylinder(h = insert_length + 1.0, d = max(10, boss_d));
        }
        for (i = [0:3]) {
            x = (i - 1.5)*12;
            translate([x, 0, 6 + insert_length + 1.0 -
                       (insert_length + insert_bottom_clearance)])
                cylinder(h = insert_length + insert_bottom_clearance + eps,
                         d = sizes[i]);
            translate([x, 0, 6 + insert_length + 1.0 -
                       insert_flange_recess_depth])
                cylinder(h = insert_flange_recess_depth + eps,
                         d = insert_flange_recess_d);
        }
    }
}

module reference_board() {
    color([0.08, 0.35, 0.12, 0.65])
        difference() {
            translate([-board_size[0]/2, -board_size[1]/2, board_bottom_z])
                cube([board_size[0], board_size[1], board_thickness]);
            for (p = board_mount_holes)
                translate([p[0], p[1], board_bottom_z - eps])
                    cylinder(h = board_thickness + 2*eps, d = 3.2);
        }
}

module base_part() {
    if (topology == "split_shell") split_base();
    else panel_base();
}

module lid_assembled() {
    if (topology == "split_shell") split_lid_assembled();
    else panel_lid_assembled();
}

module lid_print() {
    translate([0, 0, overall_z]) rotate([180, 0, 0]) lid_assembled();
}

// Fixed collision/export selector.  This is deliberately distinct from the
// exploded, optionally board-populated assembly review view below.
module installed_case() {
    base_part();
    lid_assembled();
    if (topology == "base_lid_panels") {
        assembled_panel("north"); assembled_panel("south");
        assembled_panel("east"); assembled_panel("west");
    }
}

module assembly() {
    base_part();
    translate([0, 0, explode]) lid_assembled();
    if (topology == "base_lid_panels") {
        assembled_panel("north"); assembled_panel("south");
        assembled_panel("east"); assembled_panel("west");
    }
    if (show_reference_board) reference_board();
}

selector_known = part == "base" || part == "lid" ||
    part == "insert_coupon" || part == "panel_north" ||
    part == "panel_south" || part == "panel_east" ||
    part == "panel_west" || part == "installed_case" ||
    part == "assembly";

assert(selector_known, str("Unknown pcb-enclosure selector: ", part));
echo(str("PCB_ENCLOSURE_SELECTOR_OK:", part));
echo(str("PCB_ENCLOSURE_FASTENER_STRATEGY:", fastener_strategy));

if (part == "base") base_part();
else if (part == "lid") lid_print();
else if (part == "insert_coupon") insert_coupon();
else if (part == "panel_north") flat_panel("north");
else if (part == "panel_south") flat_panel("south");
else if (part == "panel_east") flat_panel("east");
else if (part == "panel_west") flat_panel("west");
else if (part == "installed_case") installed_case();
else if (part == "assembly") assembly();
