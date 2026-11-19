// =====================================================================
//  Juice spectrophotometer: enclosure v3 (body + lid + base tray)
//  OpenSCAD, units = mm.  Licence: CERN-OHL-S-2.0
//
//  Changes from v2:
//   1. Sensor apertures are now TALL SLOTS, not round holes, so the chip
//      lines up even if as_chip_z is a couple of mm out.
//   2. Breadboard pocket: +4 mm each side, +2 mm on the length.
//   3. Bigger cable notches, and a channel so the sensor leads reach the
//      breadboard without strain.
//  Cuvette well is UNCHANGED from the fit test that worked.
//
//  part = "all" | "body" | "lid" | "base"
//  Print flat side down, no supports, black PLA.
// =====================================================================

part = "body";

// ---------- Cuvette: unchanged, this fit was good ----------
cuv        = 12.0;
clearance  = 0.4;
well       = cuv + 2*clearance;
floor_t    = 3;
beam_h     = 15;
zb         = floor_t + beam_h;
H          = 38;
wall       = 2;

// ---------- Apertures ----------
ap_d       = 2.5;        // LED-side round aperture
ap_wall    = 1.5;
ap_slot_h  = 9;          // sensor aperture: total slot height (tolerance for chip position)
tsl_slot_w = 4.0;        // TSL2591 slot width
tsl_slot_h = 10;

// ---------- LEDs ----------
cav_len    = 12;  cav_hh = 4;
led_r      = well/2 + ap_wall + cav_len;
led_ang    = 18;
d5 = 5.2;  d5f = 6.2;  len5 = 7.6;
d3 = 3.2;  d3f = 4.2;  len3 = 5.3;

// ---------- AS7343 (Pimoroni, about 20 x 20 mm) ----------
as_w        = 20;
as_t        = 1.6;
as_front    = 4.0;
as_back     = 1.0;
fit         = 0.6;
as_chip_z   = 11.0;      // chip centre above the board's BOTTOM edge, as installed.
                         // v2 used 8.5 and the chip sat too high. MEASURE and refine;
                         // the slot aperture tolerates about +/-3 mm of error.
as_chip_rt  = 0;         // chip offset right of the board centre (negative = left)
as_tin      = 4;

// ---------- TSL2591 (not yet fitted; Adafruit 25.4 x 17.8 mm) ----------
ts_w        = 17.8;
ts_t        = 1.6;
ts_front    = 3.5;
ts_back     = 1.0;
ts_chip_z   = 12.7;
ts_tin      = 3.5;

// ---------- Cable exits ----------
notch_w     = 16;        // wider than v2
notch_d     = 9;

// ---------- Lid ----------
lid_t       = 2;
hood_h      = 12;

// ---------- Breadboard + tray ----------
bb_L        = 160;       // measured breadboard length
bb_W        = 46;        // measured breadboard width
bb_side_gap = 4;         // NEW: extra clearance on EACH side
bb_end_gap  = 2;         // NEW: extra clearance on the length
base_t      = 3;
rim_h       = 8;
splash_h    = 22;
slot_w      = 14;        // wire slots through the splash wall
leg_gap     = 24;        // space behind the body for LED legs and jumpers

// ---------- Derived ----------
ax0   = well/2 + as_tin;
ax1   = ax0 + as_front + as_t + fit + as_back;
as_c  = as_chip_rt;
ty0   = well/2 + ts_tin;
ty1   = ty0 + ts_front + ts_t + fit + ts_back;
x_min = -(led_r + len5 + 3);
x_max = ax1 + wall;
y_min = min(as_c - (as_w + fit)/2 - wall, -(-x_min)*sin(led_ang) - 4);
y_max = max(ty1 + wall, as_c + (as_w + fit)/2 + wall);
cav_w = 2*led_r*sin(led_ang) + 6;
bL    = x_max - x_min;
bW    = y_max - y_min;

bbx   = bb_L + bb_end_gap;              // breadboard pocket length
bby   = bb_W + 2*bb_side_gap;           // breadboard pocket width
inW   = max(bby, bW + 1);
Wtot  = inW + 2*wall;
body_x0 = wall + bbx + wall + leg_gap;
Ltot  = body_x0 + bL + 0.6 + wall;
body_y0 = (Wtot - bW)/2;

$fn = 64;

// Horizontal bore that is a vertical slot: width d, total height h
module slot_bore(x0, len, d, h) {
    hull() {
        translate([x0, 0, zb - (h - d)/2]) rotate([0, 90, 0]) cylinder(d = d, h = len);
        translate([x0, 0, zb + (h - d)/2]) rotate([0, 90, 0]) cylinder(d = d, h = len);
    }
}
module slot_bore_y(y0, len, d, h) {
    hull() {
        translate([0, y0, zb - (h - d)/2]) rotate([-90, 0, 0]) cylinder(d = d, h = len);
        translate([0, y0, zb + (h - d)/2]) rotate([-90, 0, 0]) cylinder(d = d, h = len);
    }
}
module led_hole(d, df, len, a) {
    translate([0, 0, zb]) rotate([0, 0, 180 + a]) {
        translate([led_r - 0.5, 0, 0]) rotate([0, 90, 0]) cylinder(d = d,  h = len + 0.51);
        translate([led_r + len, 0, 0]) rotate([0, 90, 0]) cylinder(d = df, h = 40);
    }
}

// ---------- 1. Optical body ----------
module body() {
    difference() {
        translate([x_min, y_min, 0]) cube([bL, bW, H]);

        // Cuvette well (unchanged)
        translate([-well/2, -well/2, floor_t]) cube([well, well, H]);

        // LED cavity and the three LED bores
        translate([-led_r, -cav_w/2, zb - cav_hh]) cube([cav_len, cav_w, 2*cav_hh]);
        led_hole(d5, d5f, len5,  0);
        led_hole(d5, d5f, len5,  led_ang);
        led_hole(d3, d3f, len3, -led_ang);

        // Aperture: LED cavity -> cuvette (round, the LED position is fixed)
        translate([-well/2 - ap_wall - 0.1, 0, zb])
            rotate([0, 90, 0]) cylinder(d = ap_d, h = ap_wall + 0.2);

        // Aperture: cuvette -> AS7343, TALL SLOT
        slot_bore(well/2 - 0.1, as_tin + 0.2, ap_d, ap_slot_h);

        // AS7343 bay + cable notch
        translate([ax0, as_c - (as_w + fit)/2, zb - as_chip_z]) cube([ax1 - ax0, as_w + fit, H]);
        translate([ax1 - 0.1, as_c - notch_w/2, H - notch_d]) cube([wall + 0.2, notch_w, notch_d + 0.1]);

        // Aperture: cuvette -> TSL2591, TALL SLOT
        slot_bore_y(well/2 - 0.1, ts_tin + 0.2, tsl_slot_w, tsl_slot_h);

        // TSL2591 bay + cable notch
        translate([-(ts_w + fit)/2, ty0, zb - ts_chip_z]) cube([ts_w + fit, ty1 - ty0, H]);
        translate([-notch_w/2, ty1 - 0.1, H - notch_d]) cube([notch_w, wall + 0.2, notch_d + 0.1]);
    }
}

// ---------- 2. Lid ----------
module lid() {
    hood_o = well + 2*(0.6 + wall);
    difference() {
        union() {
            translate([x_min, y_min, H]) cube([bL, bW, lid_t]);
            translate([-hood_o/2, -hood_o/2, H]) cube([hood_o, hood_o, hood_h + lid_t]);
        }
        translate([-(well + 1.2)/2, -(well + 1.2)/2, H - 0.1])
            cube([well + 1.2, well + 1.2, hood_h + 0.1]);
    }
}

// ---------- 3. Base tray ----------
module base() {
    difference() {
        union() {
            cube([Ltot, Wtot, base_t]);
            difference() {
                cube([Ltot, Wtot, base_t + rim_h]);
                translate([wall, wall, base_t]) cube([Ltot - 2*wall, Wtot - 2*wall, rim_h + 1]);
            }
            translate([wall + bbx, 0, 0]) cube([wall, Wtot, base_t + splash_h]);
            translate([wall + bbx + wall, wall, 0])
                cube([Ltot - (wall + bbx + wall) - wall, body_y0 - 0.3 - wall, base_t + rim_h]);
            translate([wall + bbx + wall, body_y0 + bW + 0.3, 0])
                cube([Ltot - (wall + bbx + wall) - wall, Wtot - wall - (body_y0 + bW + 0.3), base_t + rim_h]);
        }
        for (yy = [Wtot/2 - 14, Wtot/2 + 14])
            translate([wall + bbx - 0.1, yy - slot_w/2, base_t + splash_h - 13])
                cube([wall + 0.2, slot_w, 13.1]);
        translate([-0.1, Wtot/2 - 9, base_t + 2]) cube([wall + 0.2, 18, rim_h]);
    }
}

if (part == "body") body();
else if (part == "lid") translate([0, 0, -H]) lid();
else if (part == "base") base();
else {
    color("dimgray") base();
    translate([body_x0 + 0.3 - x_min, body_y0 - y_min, base_t]) {
        color("black") body();
        color("gray") translate([0, 0, 0]) lid();
    }
}

echo(str("Body ", bL, " x ", bW, " x ", H, "   Tray ", Ltot, " x ", Wtot,
         "   Breadboard pocket ", bbx, " x ", bby));