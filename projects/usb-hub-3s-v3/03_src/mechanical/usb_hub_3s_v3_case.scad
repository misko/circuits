/*
 * USB Hub 3S v3 v1.12 enclosure — reviewed authored OpenSCAD authority.
 *
 * The complete PCB is retained on H1-H4 before the one-piece wall lid lowers
 * vertically over it.  Five edge-connector notches remain open through the
 * bottom of their side skirts for that full-body motion.  Four independent
 * base posts receive the top-down case screws and never retain the PCB.
 *
 * The fixed selector part="installed_case" emits only the installed enclosure
 * solids for collision checks.  Printable selectors are base, lid, and
 * insert_coupon.  Exact component coverage is incomplete in the immutable
 * v1.12 STEP, so this authored geometry remains a review candidate.
 */
part = "assembly";
explode = 40;
show_reference_board = true;
topology = "split_shell";

board_size = [130, 92];
board_thickness = 1.6;
board_mount_holes = [[-59, 40], [-59, -40], [21, 42], [59, -26]];
case_holes = [[-70, -51], [-70, 51], [70, -51], [70, 51]];
xy_clearance = 8;
wall = 2.4;
floor = 2.4;
roof = 2.4;
corner_radius = 4.4;
board_bottom_z = 9.5;
inside_top_z = 27;
seam_z = 10.7;
process_minimum_wall = 1.2;
skirt_bottom_clearance = 0.3;
skirt_bottom_z = floor + skirt_bottom_clearance;
skirt_plane_x = board_size[0] / 2 + 3.5;
skirt_plane_y = board_size[1] / 2 + 3.5;
skirt_span_x = 130.4;
skirt_span_y = 92.4;
case_post_top_z = inside_top_z;
roof_bearing_z = inside_top_z;
skirt_roof_overlap = 0.3;
skirt_height = roof_bearing_z + skirt_roof_overlap - skirt_bottom_z;
skirt_center_z = skirt_bottom_z + skirt_height / 2;

boss_d = 9;
case_post_d = 9;
// D4.25 is a transferred same-hardware/process coupon prior, not a physical
// result for this enclosure.  The bracketed coupon remains mandatory.
insert_hole_d = 4.25;
insert_flange_recess_d = 6.1;
insert_flange_recess_depth = 0.6;
insert_length = 4.775;
insert_bottom_clearance = 0.7;
screw_clearance_d = 3.5;
screw_head_d = 6.3;
screw_head_recess_depth = 1;

ports = [
    ["xt60-input", "J1", "west", "opening", -65, 25.6, 15.1,
     "arch", 22, 15],
    ["usb-a-1", "J2", "east", "opening", 65, 31.5, 14.5,
     "rect", 20, 12],
    ["usb-a-2", "J3", "east", "opening", 65, 9.5, 14.5,
     "rect", 20, 12],
    ["usb-a-3", "J4", "east", "opening", 65, -12.5, 14.5,
     "rect", 20, 12],
    ["usb-c-output", "J5", "south", "opening", 35, -46, 13.25,
     "arch", 17, 11],
    ["blade-fuse-service", "F1", "top", "service_opening", -45.04,
     8.3, 27, "arch", 26, 18],
    ["power-switch", "SW1", "top", "service_opening", -19, 8, 27,
     "arch", 16, 12],
    ["output-polyfuse", "F2", "top", "internal", 29, -24, 12.9,
     "none", 0, 0],
    ["master-status-led", "D8", "top", "service_opening", -31.5, 13,
     27, "round", 3.2, 3.2],
    ["usb-a-1-status-led", "D9", "top", "service_opening", 39, 39.5,
     27, "round", 3.2, 3.2],
    ["usb-a-2-status-led", "D10", "top", "service_opening", 39, 18,
     27, "round", 3.2, 3.2],
    ["usb-a-3-status-led", "D11", "top", "service_opening", 39, -4,
     27, "round", 3.2, 3.2],
    ["usb-c-status-led", "D12", "top", "service_opening", 22, -36,
     27, "round", 3.2, 3.2]
];

vents = [
    [-8, 31, 5, 34, 2, 5, "x"],
    [-8, -12, 5, 34, 2, 5, "x"],
    [27, 8, 6, 18, 2, 5, "x"],
    [20, -23, 4, 20, 2, 5, "x"]
];
vent_service_ligament_min = 1.2;
side_notch_ligament_min = 1.2;
post_skirt_clearance_min = 0.3;

$fn = 48;
eps = 0.05;

inner_size = [
    board_size[0] + 2 * xy_clearance,
    board_size[1] + 2 * xy_clearance
];
outer_size = [inner_size[0] + 2 * wall, inner_size[1] + 2 * wall];
overall_z = inside_top_z + roof;

function side_span(side) =
    side == "north" || side == "south" ? skirt_span_x : skirt_span_y;

function port_u(port) =
    port[2] == "north" || port[2] == "south" ? port[4] : port[5];

function skirt_transform(side) =
    side == "north" ?
        [[1,0,0,0], [0,0,-1,skirt_plane_y+wall/2],
         [0,1,0,skirt_center_z], [0,0,0,1]] :
    side == "south" ?
        [[1,0,0,0], [0,0,-1,-skirt_plane_y+wall/2],
         [0,1,0,skirt_center_z], [0,0,0,1]] :
    side == "east" ?
        [[0,0,-1,skirt_plane_x+wall/2], [1,0,0,0],
         [0,1,0,skirt_center_z], [0,0,0,1]] :
        [[0,0,1,-skirt_plane_x-wall/2], [1,0,0,0],
         [0,1,0,skirt_center_z], [0,0,0,1]];

function transform_point(matrix, point) = [
    matrix[0][0]*point[0] + matrix[0][1]*point[1] +
        matrix[0][2]*point[2] + matrix[0][3],
    matrix[1][0]*point[0] + matrix[1][1]*point[1] +
        matrix[1][2]*point[2] + matrix[1][3],
    matrix[2][0]*point[0] + matrix[2][1]*point[1] +
        matrix[2][2]*point[2] + matrix[2][3]
];

function vector_error(a, b) =
    sqrt(pow(a[0]-b[0], 2) + pow(a[1]-b[1], 2) + pow(a[2]-b[2], 2));

function skirt_expected_center(side) =
    side == "north" ? [0, skirt_plane_y, skirt_center_z] :
    side == "south" ? [0, -skirt_plane_y, skirt_center_z] :
    side == "east" ? [skirt_plane_x, 0, skirt_center_z] :
    [-skirt_plane_x, 0, skirt_center_z];

function opening_expected_center(port) =
    port[2] == "north" ? [port[4], skirt_plane_y, port[6]] :
    port[2] == "south" ? [port[4], -skirt_plane_y, port[6]] :
    port[2] == "east" ? [skirt_plane_x, port[5], port[6]] :
    [-skirt_plane_x, port[5], port[6]];

function opening_local_center(port) = [
    port_u(port), port[6] - skirt_center_z, wall/2
];

function bounds_clearance(center_a, half_a, center_b, half_b) =
    let(dx = max(abs(center_a[0] - center_b[0]) - half_a[0] - half_b[0], 0),
        dy = max(abs(center_a[1] - center_b[1]) - half_a[1] - half_b[1], 0))
    sqrt(dx*dx + dy*dy);

function vent_slot_center(vent, i) =
    let(offset = (i - (vent[2] - 1) / 2) * vent[5])
    [vent[0] + (vent[6] == "y" ? offset : 0),
     vent[1] + (vent[6] == "x" ? offset : 0)];

function vent_slot_half_size(vent) =
    vent[6] == "x" ? [vent[3]/2, vent[4]/2]
                     : [vent[4]/2, vent[3]/2];

side_ports = [for (port = ports)
    if (port[3] == "opening" && port[2] != "top") port];
top_service_ports = [for (port = ports)
    if (port[3] == "service_opening" && port[2] == "top") port];
skirt_sides = ["north", "south", "east", "west"];

skirt_center_errors = [for (side = skirt_sides)
    vector_error(
        transform_point(skirt_transform(side), [0, 0, wall/2]),
        skirt_expected_center(side))];
skirt_vertical_errors = [for (side = skirt_sides)
    let(origin = transform_point(skirt_transform(side), [0, 0, wall/2]),
        vertical = transform_point(skirt_transform(side), [0, 1, wall/2]))
    vector_error(
        [vertical[0]-origin[0], vertical[1]-origin[1],
         vertical[2]-origin[2]], [0, 0, 1])];
opening_center_errors = [for (port = side_ports)
    vector_error(
        transform_point(skirt_transform(port[2]), opening_local_center(port)),
        opening_expected_center(port))];
opening_top_errors = [for (port = side_ports)
    abs(transform_point(skirt_transform(port[2]), [
        port_u(port), port[6]-skirt_center_z+port[9]/2, wall/2
    ])[2] - (port[6]+port[9]/2))];
opening_bottom_errors = [for (port = side_ports)
    abs(transform_point(skirt_transform(port[2]), [
        port_u(port), -skirt_height/2-eps, wall/2
    ])[2] - (skirt_bottom_z-eps))];
opening_top_ligaments = [for (port = side_ports)
    inside_top_z - (port[6] + port[9]/2)];
opening_end_ligaments = [for (port = side_ports)
    side_span(port[2])/2 - abs(port_u(port)) - port[8]/2];
opening_pair_ligaments = [for (a = side_ports) for (b = side_ports)
    if (a[1] < b[1] && a[2] == b[2])
        abs(port_u(a)-port_u(b)) - (a[8]+b[8])/2];

vent_service_ligaments = [
    for (vent = vents)
        for (i = [0:vent[2]-1])
            for (port = top_service_ports)
                bounds_clearance(
                    vent_slot_center(vent, i), vent_slot_half_size(vent),
                    [port[4], port[5]], [port[8]/2, port[9]/2])
];

post_skirt_clearance_x =
    abs(case_holes[2][0]) - skirt_span_x/2 - case_post_d/2;
post_skirt_clearance_y =
    abs(case_holes[2][1]) - skirt_span_y/2 - case_post_d/2;

assert(wall + 1e-6 >= process_minimum_wall,
       "active skirt wall is below the declared process minimum");
assert(roof + 1e-6 >= process_minimum_wall,
       "roof is below the declared process minimum");
assert(abs(case_post_top_z-roof_bearing_z) < 1e-6,
       "case posts and lid roof must meet at the intended bearing plane");
assert(skirt_roof_overlap > 0,
       "lid skirts must overlap the roof to remain one printable solid");
assert(max(skirt_center_errors) < 1e-6,
       "skirt transform does not center its declared wall plane");
assert(max(skirt_vertical_errors) < 1e-6,
       "skirt transform does not map local vertical to global +Z");
assert(max(opening_center_errors) < 1e-6,
       "side notch center does not match its declared tangent/Z coordinates");
assert(max(opening_top_errors) < 1e-6,
       "side notch top does not match its declared top");
assert(max(opening_bottom_errors) < 1e-6,
       "side notch does not reach through the skirt bottom");
assert(min(opening_top_ligaments) + 1e-6 >= process_minimum_wall,
       "side notch leaves too little material below the roof");
assert(min(opening_end_ligaments) + 1e-6 >= side_notch_ligament_min,
       "side notch leaves too little material at a skirt end");
assert(min(opening_pair_ligaments) + 1e-6 >= side_notch_ligament_min,
       "adjacent side notches leave too little skirt ligament");
assert(post_skirt_clearance_x + 1e-6 >= post_skirt_clearance_min,
       "north/south skirt endpoint is too close to a case post");
assert(post_skirt_clearance_y + 1e-6 >= post_skirt_clearance_min,
       "east/west skirt endpoint is too close to a case post");
assert(min(vent_service_ligaments) + 1e-6 >=
       vent_service_ligament_min,
       "vent-to-service-opening ligament is below declaration");

echo(str("LID_SKIRT_CENSUS sides=", len(skirt_sides),
         " bottom_open_notches=", len(side_ports),
         " max_center_error_mm=", max(opening_center_errors),
         " min_top_ligament_mm=", min(opening_top_ligaments),
         " min_pair_ligament_mm=", min(opening_pair_ligaments),
         " min_post_clearance_mm=",
         min(post_skirt_clearance_x, post_skirt_clearance_y)));
echo(str("VENT_SERVICE_LIGAMENT_CENSUS pairs=",
         len(vent_service_ligaments),
         " conservative_min_mm=", min(vent_service_ligaments),
         " required_mm=", vent_service_ligament_min));

module rounded_rect_2d(size, radius) {
    rr = min(radius, min(size[0], size[1]) / 2 - 0.01);
    offset(r = rr)
        square([size[0] - 2*rr, size[1] - 2*rr], center = true);
}

module access_profile_2d(w, h, shape) {
    if (shape == "round") {
        circle(d = min(w, h));
    } else if (shape == "arch") {
        flat = min(w / 3, 4.0);
        slope = min((w - flat) / 2, h / 2);
        polygon([
            [-w/2, -h/2], [w/2, -h/2],
            [w/2, h/2-slope], [flat/2, h/2],
            [-flat/2, h/2], [-w/2, h/2-slope]
        ]);
    } else {
        square([w, h], center = true);
    }
}

module bottom_open_profile_2d(w, h, shape, bottom_y) {
    if (shape == "arch") {
        flat = min(w / 3, 4.0);
        slope = min((w - flat) / 2, h / 2);
        polygon([
            [-w/2, bottom_y], [w/2, bottom_y],
            [w/2, h/2-slope], [flat/2, h/2],
            [-flat/2, h/2], [-w/2, h/2-slope]
        ]);
    } else {
        polygon([
            [-w/2, bottom_y], [w/2, bottom_y],
            [w/2, h/2], [-w/2, h/2]
        ]);
    }
}

module top_access_cuts() {
    for (port = top_service_ports)
        translate([port[4], port[5], inside_top_z-eps])
            linear_extrude(height = roof + 2*eps)
                access_profile_2d(port[8], port[9], port[7]);
    for (vent = vents) {
        for (i = [0:vent[2]-1]) {
            center = vent_slot_center(vent, i);
            half = vent_slot_half_size(vent);
            translate([center[0], center[1], inside_top_z-eps])
                linear_extrude(height = roof + 2*eps)
                    rounded_rect_2d([2*half[0], 2*half[1]], vent[4]/2);
        }
    }
}

module boss_set(points, diameter, top_z) {
    for (point = points)
        translate([point[0], point[1], floor-eps])
            cylinder(h = top_z-floor+eps, d = diameter);
}

module insert_pocket_set(points, top_z) {
    depth = insert_length + insert_bottom_clearance;
    for (point = points) {
        translate([point[0], point[1], top_z-depth])
            cylinder(h = depth+eps, d = insert_hole_d);
        translate([point[0], point[1], top_z-insert_flange_recess_depth])
            cylinder(h = insert_flange_recess_depth+eps,
                     d = insert_flange_recess_d);
    }
}

module base_part() {
    difference() {
        union() {
            linear_extrude(height = floor)
                rounded_rect_2d(outer_size, corner_radius);
            boss_set(board_mount_holes, boss_d, board_bottom_z);
            boss_set(case_holes, case_post_d, case_post_top_z);
        }
        insert_pocket_set(board_mount_holes, board_bottom_z);
        insert_pocket_set(case_holes, case_post_top_z);
    }
}

module flat_skirt(side) {
    span = side_span(side);
    linear_extrude(height = wall)
        difference() {
            square([span, skirt_height], center = true);
            for (port = side_ports)
                if (port[2] == side)
                    translate([port_u(port), port[6]-skirt_center_z])
                        bottom_open_profile_2d(
                            port[8], port[9], port[7],
                            skirt_bottom_z-port[6]-eps);
        }
}

module assembled_skirt(side) {
    multmatrix(skirt_transform(side)) flat_skirt(side);
}

module lid_fastener_cuts() {
    bearing_z = overall_z - screw_head_recess_depth;
    for (point = case_holes) {
        translate([point[0], point[1], inside_top_z-eps])
            cylinder(h = roof+2*eps, d = screw_clearance_d);
        translate([point[0], point[1], bearing_z])
            cylinder(h = overall_z-bearing_z+eps, d = screw_head_d);
    }
}

module lid_assembled() {
    difference() {
        union() {
            translate([0, 0, roof_bearing_z])
                linear_extrude(height = roof)
                    rounded_rect_2d(outer_size, corner_radius);
            assembled_skirt("north");
            assembled_skirt("south");
            assembled_skirt("east");
            assembled_skirt("west");
        }
        top_access_cuts();
        lid_fastener_cuts();
    }
}

module lid_print() {
    translate([0, 0, overall_z]) rotate([180, 0, 0]) lid_assembled();
}

module insert_coupon() {
    sizes = [4.05, 4.15, 4.25, 4.35, 4.45];
    labels = ["4.05", "4.15", "4.25", "4.35", "4.45"];
    difference() {
        union() {
            translate([-36, -12, 0]) cube([72, 24, 6]);
            for (i = [0:4])
                translate([(i-2)*13, 1.5, 6-eps])
                    cylinder(h = insert_length+1.0, d = max(10, boss_d));
        }
        for (i = [0:4]) {
            x = (i-2)*13;
            translate([x, 1.5, 6+insert_length+1.0-
                       (insert_length+insert_bottom_clearance)])
                cylinder(h = insert_length+insert_bottom_clearance+eps,
                         d = sizes[i]);
            translate([x, 1.5, 6+insert_length+1.0-
                       insert_flange_recess_depth])
                cylinder(h = insert_flange_recess_depth+eps,
                         d = insert_flange_recess_d);
            translate([x, -8.3, 5.55])
                linear_extrude(height = 0.55)
                    text(labels[i], size = 3.0,
                         halign = "center", valign = "center");
        }
    }
}

module reference_board() {
    color([0.08, 0.35, 0.12, 0.65])
        difference() {
            translate([-board_size[0]/2, -board_size[1]/2, board_bottom_z])
                cube([board_size[0], board_size[1], board_thickness]);
            for (point = board_mount_holes)
                translate([point[0], point[1], board_bottom_z-eps])
                    cylinder(h = board_thickness+2*eps, d = 3.2);
        }
}

module installed_case() {
    base_part();
    lid_assembled();
}

module assembly() {
    base_part();
    translate([0, 0, explode]) lid_assembled();
    if (show_reference_board) reference_board();
}

module base_review() {
    base_part();
    if (show_reference_board) reference_board();
}

module closed_review() {
    installed_case();
    if (show_reference_board) reference_board();
}

if (part == "base") base_part();
else if (part == "lid") lid_print();
else if (part == "insert_coupon") insert_coupon();
else if (part == "installed_case") installed_case();
else if (part == "assembly") assembly();
else if (part == "base_review") base_review();
else if (part == "closed_review") closed_review();
else assert(false, str("Unknown enclosure part selector: ", part));
