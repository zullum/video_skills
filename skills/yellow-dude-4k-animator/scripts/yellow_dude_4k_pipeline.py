import os
import math
import shutil
import subprocess
import cv2
import numpy as np
from scipy.spatial import Delaunay
from PIL import Image, ImageDraw, ImageFont

# Usage: python yellow_dude_4k_pipeline.py [POSE_SHEET]
#   POSE_SHEET  pose sheet image, poses side by side (Pose 1 | Pose 2 | Pose 3 | ...).
#               Default: ../assets/pullup_poses.jpg (4-pose pull-up example). Also settable via YD_RAW_SHEET.
#               Any size works: the sheet is resized to 1376 px wide (Gemini 16:9 1K), which the pose crops expect.
# Other env vars:
#   YD_OUT_DIR    output folder (default ./yd_output)
#   YD_INT_DIR    intermediate folder (default ./yd_intermediate)
#   YD_AUDIO      WAV for the video (optional; silent video if missing)
#   YD_REF_IMG_2  reference image for the before/after comparison (optional; skipped if missing)
import sys
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_SHEET = (sys.argv[1] if len(sys.argv) > 1 else
             os.environ.get("YD_RAW_SHEET", os.path.join(SKILL_DIR, "assets", "pullup_poses.jpg")))
OUT_DIR = os.environ.get("YD_OUT_DIR", "yd_output")
INT_DIR = os.environ.get("YD_INT_DIR", "yd_intermediate")
os.makedirs(OUT_DIR, exist_ok=True)
FRAMES_V15_DIR = os.path.join(INT_DIR, "frames_24_v15_flawless")
os.makedirs(FRAMES_V15_DIR, exist_ok=True)

AUDIO_WAV = os.environ.get("YD_AUDIO", os.path.join(INT_DIR, "yellow_dude_30s_audio.wav"))
USER_IMG_1 = os.environ.get("YD_REF_IMG_1", "ref1.jpg")
USER_IMG_2 = os.environ.get("YD_REF_IMG_2", "ref2.jpg")

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

CW, CH = 480, 820
BAR_Y = 92
UNIFORM_S = 100.0 / 124.0
LOCKED_LX = 156.0
LOCKED_RX = 324.0

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

raw_bgr = cv2.imread(RAW_SHEET)
if raw_bgr is None:
    sys.exit(f"Cannot read pose sheet: {RAW_SHEET}")
SHEET_W = 1376  # pose crop columns below are tuned for this width
if raw_bgr.shape[1] != SHEET_W:
    _h = round(raw_bgr.shape[0] * SHEET_W / raw_bgr.shape[1])
    raw_bgr = cv2.resize(raw_bgr, (SHEET_W, _h), interpolation=cv2.INTER_LANCZOS4)
raw_rgb = cv2.cvtColor(raw_bgr, cv2.COLOR_BGR2RGB)

def extract_clean_4x_pose_perfect(x0, x1, is_pose3=False):
    sub = raw_rgb[:, x0:x1].copy()
    h0, w0, _ = sub.shape
    r0, g0, b0 = sub[:, :, 0].astype(int), sub[:, :, 1].astype(int), sub[:, :, 2].astype(int)

    yellow0 = ((r0 - b0) > 45) & (r0 > 140)
    cx0 = int(np.median(np.where(yellow0)[1]))
    hy_top0 = int(np.where(yellow0[:, cx0])[0].min())

    yy0, xx0 = np.mgrid[0:h0, 0:w0]
    eye_zone0 = (np.abs(xx0 - cx0) < 26) & (yy0 >= hy_top0 + 14) & (yy0 <= hy_top0 + 48)
    head_col0 = (np.abs(xx0 - cx0) < 32) & (yy0 >= hy_top0 - 4)

    is_bar0 = (yy0 < 215) & (~eye_zone0) & (~head_col0) & (np.abs(r0 - g0) < 20) & (np.abs(g0 - b0) < 20) & (r0 > 65)
    sub[is_bar0] = [255, 255, 255]

    ff1 = np.zeros((h0 + 2, w0 + 2), np.uint8)
    tmp1 = sub.copy()
    for sx in [0, w0 - 1, w0 // 2]:
        for sy in [0, h0 - 1]:
            if tmp1[sy, sx, 0] > 210:
                cv2.floodFill(tmp1, ff1, (sx, sy), (255, 255, 255), (28, 28, 28), (28, 28, 28), cv2.FLOODFILL_FIXED_RANGE)
    bg1 = ff1[1:-1, 1:-1] > 0

    if is_pose3:
        r1 = sub[:, :, 0].astype(int)
        g1 = sub[:, :, 1].astype(int)
        b1 = sub[:, :, 2].astype(int)
        is_black_ink = (r1 < 105) & (g1 < 95) & (b1 < 95)
        can_eat = (~is_black_ink) & (yy0 >= 145) & (yy0 <= 420)
        kernel3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        for _ in range(14):
            dil = cv2.dilate(bg1.astype(np.uint8), kernel3) > 0
            bg1 = bg1 | (dil & can_eat)
        sub[bg1] = [255, 255, 255]

    scale = 4
    sw, sh = w0 * scale, h0 * scale
    rgb_4k = cv2.resize(sub, (sw, sh), interpolation=cv2.INTER_LANCZOS4)
    rgb_4k = cv2.bilateralFilter(rgb_4k, d=9, sigmaColor=45, sigmaSpace=9)

    ff_mask = np.zeros((sh + 2, sw + 2), np.uint8)
    temp = rgb_4k.copy()
    for sx in [0, sw - 1, sw // 2]:
        for sy in [0, sh - 1]:
            if temp[sy, sx, 0] > 210:
                cv2.floodFill(temp, ff_mask, (sx, sy), (255, 255, 255), (28, 28, 28), (28, 28, 28), cv2.FLOODFILL_FIXED_RANGE)

    cx_4k = cx0 * scale
    for y_leg_1x in range(445, 742, 6):
        py = min(sh - 1, y_leg_1x * scale)
        for dx_probe in [0, -8, 8, -16, 16]:
            px = max(0, min(sw - 1, cx_4k + dx_probe))
            if temp[py, px, 0] > 205 and temp[py, px, 2] > 195 and ff_mask[py + 1, px + 1] == 0:
                cv2.floodFill(temp, ff_mask, (px, py), (255, 255, 255), (28, 28, 28), (28, 28, 28), cv2.FLOODFILL_FIXED_RANGE)

    for y_arm_1x in range(60, 210, 8):
        py = min(sh - 1, y_arm_1x * scale)
        for dx_1x in [-48, 48, -58, 58]:
            px = max(0, min(sw - 1, (cx0 + dx_1x) * scale))
            if temp[py, px, 0] > 215 and temp[py, px, 2] > 205 and ff_mask[py + 1, px + 1] == 0:
                cv2.floodFill(temp, ff_mask, (px, py), (255, 255, 255), (28, 28, 28), (28, 28, 28), cv2.FLOODFILL_FIXED_RANGE)

    bg_mask = ff_mask[1:-1, 1:-1] > 0
    fg_mask = (~bg_mask).astype(np.uint8)
    num_l, labels, stats, _ = cv2.connectedComponentsWithStats(fg_mask, connectivity=8)
    main_fg = np.zeros_like(fg_mask)
    for lbl in range(1, num_l):
        if stats[lbl, cv2.CC_STAT_AREA] > 20000:
            main_fg[labels == lbl] = 1

    fg_eroded = cv2.erode(main_fg, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)), iterations=1)
    sdf_in = cv2.distanceTransform(fg_eroded, cv2.DIST_L2, 5).astype(np.float32)
    sdf_out = cv2.distanceTransform(1 - fg_eroded, cv2.DIST_L2, 5).astype(np.float32)
    sdf = cv2.GaussianBlur(sdf_in - sdf_out, (7, 7), 0)
    alpha_4k = np.clip((sdf + 1.2) / 2.4 * 255.0, 0.0, 255.0)

    r_4k, b_4k = rgb_4k[:, :, 0].astype(int), rgb_4k[:, :, 2].astype(int)
    outer_rim = (sdf > -3.0) & (sdf < 5.0) & ((r_4k - b_4k) < 50)
    rgb_4k[outer_rim] = [18, 18, 20]
    rgb_4k[alpha_4k == 0] = [18, 18, 20]

    gray_4k = cv2.cvtColor(rgb_4k, cv2.COLOR_RGB2GRAY).astype(np.float32)
    local_max = cv2.dilate(gray_4k, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    ink_ratio = np.clip((local_max - gray_4k) / np.maximum(local_max, 40.0), 0.0, 1.0)
    ink_strength = cv2.GaussianBlur(np.clip((ink_ratio - 0.18) / 0.32, 0.0, 1.0), (3, 3), 0)

    hsv = cv2.cvtColor(rgb_4k, cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.08, 0, 255)
    rgb_vib = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32)

    rgba_4k = np.zeros((sh, sw, 4), dtype=np.uint8)
    for c in range(3):
        rgba_4k[:, :, c] = np.clip(rgb_vib[:, :, c] * (1.0 - 0.85 * ink_strength) + 16.0 * (0.85 * ink_strength), 0, 255).astype(np.uint8)
    rgba_4k[:, :, 3] = alpha_4k.astype(np.uint8)
    rgba_4k[rgba_4k[:, :, 3] == 0] = [0, 0, 0, 0]

    rgba_f = rgba_4k.astype(np.float32)
    a_norm = rgba_f[:, :, 3:4] / 255.0
    premult = rgba_f[:, :, :3] * a_norm
    premult_1x = cv2.resize(premult, (w0, h0), interpolation=cv2.INTER_AREA)
    alpha_1x = cv2.resize(rgba_f[:, :, 3], (w0, h0), interpolation=cv2.INTER_AREA)
    a_1x_norm = np.maximum(alpha_1x[:, :, None] / 255.0, 1e-5)
    rgb_1x = np.clip(premult_1x / a_1x_norm, 0, 255).astype(np.uint8)
    out_1x = np.zeros((h0, w0, 4), dtype=np.uint8)
    out_1x[:, :, :3] = rgb_1x
    out_1x[:, :, 3] = np.clip(alpha_1x, 0, 255).astype(np.uint8)
    out_1x[out_1x[:, :, 3] < 16] = [0, 0, 0, 0]
    return out_1x, cx0, hy_top0

p1_rgba, cx1, hy1 = extract_clean_4x_pose_perfect(0, 335, is_pose3=False)
p2_rgba, cx2, hy2 = extract_clean_4x_pose_perfect(340, 680, is_pose3=False)
p3_rgba, cx3, hy3 = extract_clean_4x_pose_perfect(685, 1035, is_pose3=True)

# ==============================================================================
# STEP 2: SCALE ALL 3 REAL POSES BY THE EXACT SAME UNIFORM FACTOR `UNIFORM_S`
# WITHOUT OVERWRITING POSE 3'S NATIVE TUCKED LEGS OR ABS!
# Why?
# 1) Because using the SAME uniform scale `UNIFORM_S = 100.0 / 124.0 = 0.8065`
#    for Pose 1, Pose 2, AND Pose 3 guarantees that the Head (`47px` wide) and
#    Upper Body never shrink or inflate!
# 2) And keeping Pose 1, Pose 2, and Pose 3's NATIVE LEGS and NATIVE ABS preserves
#    the exact natural Hollow-Body leg bend (`noge se polako saviju kad idemo gore`)
#    from v6, while having 0% black leg bridges and 0% exterior pink glow!
# ==============================================================================

UNIFORM_S = 100.0 / 124.0

def place_native_pose_on_bar(pose_rgba, cx_p):
    h_in, w_in, _ = pose_rgba.shape
    nw, nh = int(round(w_in * UNIFORM_S)), int(round(h_in * UNIFORM_S))
    pf = pose_rgba.astype(np.float32)
    an = pf[:, :, 3:4] / 255.0
    pm = cv2.resize(pf[:, :, :3] * an, (nw, nh), interpolation=cv2.INTER_AREA)
    al = cv2.resize(pf[:, :, 3], (nw, nh), interpolation=cv2.INTER_AREA)
    scaled = np.zeros((nh, nw, 4), dtype=np.uint8)
    scaled[:, :, :3] = np.clip(pm / np.maximum(al[:, :, None] / 255.0, 1e-5), 0, 255).astype(np.uint8)
    scaled[:, :, 3] = np.clip(al, 0, 255).astype(np.uint8)
    scaled[scaled[:, :, 3] < 16] = [0, 0, 0, 0]

    cx_s = int(round(cx_p * UNIFORM_S))
    ys, xs = np.where((scaled[:, :, 3] > 128) & (np.abs(np.arange(nw)[None, :] - cx_s) > 25))
    fist_top_y = int(ys.min())
    fist_center_y = fist_top_y + 12

    out = np.zeros((CH, CW, 4), dtype=np.uint8)
    x_paste = 240 - cx_s
    y_paste = BAR_Y - fist_center_y

    for sy in range(nh):
        dy = sy + y_paste
        if 0 <= dy < CH:
            for sx in range(nw):
                dx = sx + x_paste
                if 0 <= dx < CW:
                    out[dy, dx] = scaled[sy, sx]
    return out

kp1_raw = place_native_pose_on_bar(p1_rgba, cx1)
kp2_raw = place_native_pose_on_bar(p2_rgba, cx2)
kp3_raw = place_native_pose_on_bar(p3_rgba, cx3)

# Extract the un-warped Master Head patch from kp2_raw so the skull crown never gets pointed!
hy2_s = int(np.where(kp2_raw[:, 240, 3] > 128)[0].min())
master_head_patch = kp2_raw[hy2_s - 2 : hy2_s + 58, 240 - 28 : 240 + 28].copy()

def stamp_rigid_head_only(frame_rgba, hy_f):
    """
    Stamps ONLY the un-warped Master Head at `hy_f` so the head is ALWAYS 100% round
    and constant-sized (0.0px size change), while leaving the Abs, Pelvis, Shorts,
    Thighs, Knees, Calves, and Feet free to perform the natural Hollow-Body leg bend!
    """
    out = frame_rgba.copy()
    y_h0 = max(0, hy_f - 2)
    y_clear0 = max(0, hy_f - 18)
    out[y_clear0 : y_h0 + 46, 214 : 266] = [0, 0, 0, 0]

    mh_h, mh_w, _ = master_head_patch.shape
    roi_h = out[y_h0 : y_h0 + mh_h, 240 - 28 : 240 + 28]
    m_head = master_head_patch[:, :, 3] > 64
    roi_h[m_head] = master_head_patch[m_head]
    out[y_h0 : y_h0 + mh_h, 240 - 28 : 240 + 28] = roi_h
    return out

# ==============================================================================
# STEP 3: DETECT ACTUAL ANATOMICAL LANDMARKS ON EACH POSE (INCLUDING NATIVE
# ABDOMINAL CRUNCH, SHORTS WAIST, KNEES, CALVES, AND FEET!)
# Look at why Pose 1 -> Pose 2 -> Pose 3 has natural leg bending & ab flexing:
# In Pose 1 & Pose 2: head-to-toe is 474px (legs straight in dead hang / early pull).
# In Pose 3: the knees and hips naturally flex/tuck forward (foreshortening legs by 28px
# and bringing the calves/feet slightly closer together), while the abs & obliques contract!
# ==============================================================================

def warp_piecewise_affine(img, src_pts, dst_pts, triangles):
    out = np.zeros_like(img)
    h, w, _ = img.shape
    for t in triangles:
        t_src = src_pts[t].astype(np.float32)
        t_dst = dst_pts[t].astype(np.float32)
        r_src = cv2.boundingRect(t_src)
        r_dst = cv2.boundingRect(t_dst)
        x_s, y_s, w_s, h_s = r_src
        x_d, y_d, w_d, h_d = r_dst
        if w_s <= 0 or h_s <= 0 or w_d <= 0 or h_d <= 0:
            continue
        x_s0, y_s0 = max(0, x_s), max(0, y_s)
        x_s1, y_s1 = min(w, x_s + w_s), min(h, y_s + h_s)
        x_d0, y_d0 = max(0, x_d), max(0, y_d)
        x_d1, y_d1 = min(w, x_d + w_d), min(h, y_d + h_d)
        if x_s1 <= x_s0 or y_s1 <= y_s0 or x_d1 <= x_d0 or y_d1 <= y_d0:
            continue

        t_src_loc = t_src - np.array([x_s0, y_s0], dtype=np.float32)
        t_dst_loc = t_dst - np.array([x_d0, y_d0], dtype=np.float32)
        M = cv2.getAffineTransform(t_src_loc, t_dst_loc)
        patch_src = img[y_s0:y_s1, x_s0:x_s1].astype(np.float32)
        an = patch_src[:, :, 3:4] / 255.0
        pm = patch_src[:, :, :3] * an
        w_pm = cv2.warpAffine(pm, M, (x_d1 - x_d0, y_d1 - y_d0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
        w_al = cv2.warpAffine(patch_src[:, :, 3], M, (x_d1 - x_d0, y_d1 - y_d0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
        w_patch = np.zeros((y_d1 - y_d0, x_d1 - x_d0, 4), dtype=np.uint8)
        w_patch[:, :, :3] = np.clip(w_pm / np.maximum(w_al[:, :, None] / 255.0, 1e-5), 0, 255).astype(np.uint8)
        w_patch[:, :, 3] = np.clip(w_al, 0, 255).astype(np.uint8)

        mask = np.zeros((y_d1 - y_d0, x_d1 - x_d0), dtype=np.uint8)
        cv2.fillConvexPoly(mask, np.int32(t_dst_loc), 255)
        roi = out[y_d0:y_d1, x_d0:x_d1]
        m_bool = mask > 0
        roi[m_bool] = w_patch[m_bool]
        out[y_d0:y_d1, x_d0:x_d1] = roi
    return out

def enhance_abs_and_core_contraction(frame_rgba, hy_f, sy_f, core_act):
    if core_act <= 0.04:
        return frame_rgba

    out = frame_rgba.copy()
    r = out[:, :, 0].astype(np.float32)
    g = out[:, :, 1].astype(np.float32)
    b = out[:, :, 2].astype(np.float32)
    a = out[:, :, 3].astype(np.float32)
    yy, xx = np.mgrid[0:CH, 0:CW].astype(np.float32)

    abs_cy = 0.5 * (hy_f + 112.0 + sy_f - 6.0)
    abs_half_h = max(24.0, 0.5 * (sy_f - (hy_f + 108.0)))

    is_warm_skin = (a > 200) & ((r - b) > 55.0) & (r > 130.0) & (g > 70.0)
    abs_zone = np.exp(-(((xx - 240.0) / 38.0) ** 4 + ((yy - abs_cy) / abs_half_h) ** 4))
    quad_cy = sy_f + 92.0
    quad_zone = 0.42 * (
        np.exp(-(((xx - 212.0) / 22.0) ** 2 + ((yy - quad_cy) / 42.0) ** 2)) +
        np.exp(-(((xx - 268.0) / 22.0) ** 2 + ((yy - quad_cy) / 42.0) ** 2))
    )

    w_core = np.where(is_warm_skin, np.clip((0.78 * abs_zone + quad_zone) * core_act, 0.0, 0.78), 0.0)
    r_new = np.clip(r * (1.0 - 0.06 * w_core), 0, 255)
    g_new = np.clip(g * (1.0 - 0.62 * w_core), 0, 255)
    b_new = np.clip(b * (1.0 - 0.45 * w_core) + 14.0 * w_core, 0, 255)

    gray = 0.299 * r + 0.587 * g + 0.114 * b
    local_max = cv2.dilate(gray, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    groove_contrast = np.clip((local_max - gray) / np.maximum(local_max, 40.0), 0.0, 1.0)
    in_abs_box = (a > 200) & ( np.abs(xx - 240.0) < 44.0 ) & (yy >= hy_f + 102.0) & (yy <= sy_f - 4.0)
    groove_boost = np.where(in_abs_box, np.clip((groove_contrast - 0.10) * 1.8 * core_act, 0.0, 0.65), 0.0)

    out[:, :, 0] = np.clip(r_new * (1.0 - groove_boost) + 18.0 * groove_boost, 0, 255).astype(np.uint8)
    out[:, :, 1] = np.clip(g_new * (1.0 - groove_boost) + 18.0 * groove_boost, 0, 255).astype(np.uint8)
    out[:, :, 2] = np.clip(b_new * (1.0 - groove_boost) + 20.0 * groove_boost, 0, 255).astype(np.uint8)
    return out

def blend_sdf_zero_double_lines(wA, wB, alpha):
    if alpha <= 0.001:
        return wA.copy()
    if alpha >= 0.999:
        return wB.copy()

    fA = wA.astype(np.float32)
    fB = wB.astype(np.float32)
    maskA = (fA[:, :, 3] > 127).astype(np.uint8)
    maskB = (fB[:, :, 3] > 127).astype(np.uint8)

    sdfA = cv2.distanceTransform(maskA, cv2.DIST_L2, 5).astype(np.float32) - cv2.distanceTransform(1 - maskA, cv2.DIST_L2, 5).astype(np.float32)
    sdfB = cv2.distanceTransform(maskB, cv2.DIST_L2, 5).astype(np.float32) - cv2.distanceTransform(1 - maskB, cv2.DIST_L2, 5).astype(np.float32)
    sdf_blend = cv2.GaussianBlur((1.0 - alpha) * sdfA + alpha * sdfB, (7, 7), 0)
    out_alpha = np.clip((sdf_blend + 1.0) / 2.0 * 255.0, 0.0, 255.0)

    dom_is_B = (alpha >= 0.5)
    rgb_dom = fB[:, :, :3] if dom_is_B else fA[:, :, :3]
    rgb_sec = fA[:, :, :3] if dom_is_B else fB[:, :, :3]
    sdf_dom = sdfB if dom_is_B else sdfA
    sdf_sec = sdfA if dom_is_B else sdfB

    # Dilate-fill rgb_sec outward by 12px from its valid interior (sdf_sec > 2.5) so it never has black/empty pixels near the edge
    sec_interior = (sdf_sec > 2.5).astype(np.uint8)
    inpaint_mask = (1 - sec_interior).astype(np.uint8)
    rgb_sec_filled = cv2.inpaint(rgb_sec.astype(np.uint8), inpaint_mask, 5, cv2.INPAINT_TELEA).astype(np.float32)
    dom_interior = (sdf_dom > 2.5).astype(np.uint8)
    rgb_dom_filled = cv2.inpaint(rgb_dom.astype(np.uint8), (1 - dom_interior).astype(np.uint8), 5, cv2.INPAINT_TELEA).astype(np.float32)

    sec_smooth_color = cv2.GaussianBlur(rgb_sec_filled, (9, 9), 0)
    color_mix_w = alpha if not dom_is_B else (1.0 - alpha)

    gray_dom = 0.299 * rgb_dom_filled[:, :, 0] + 0.587 * rgb_dom_filled[:, :, 1] + 0.114 * rgb_dom_filled[:, :, 2]
    # Only treat interior dark lines (sdf_dom > 3.5) as dominant ink so outer border ink of wA/wB NEVER creates a double contour!
    is_dom_ink = (gray_dom < 105.0) & (sdf_dom > 3.5)

    out_rgb = np.zeros((CH, CW, 3), dtype=np.float32)
    for c in range(3):
        c_dom = rgb_dom_filled[:, :, c]
        c_sec_col = sec_smooth_color[:, :, c]
        out_rgb[:, :, c] = np.where(is_dom_ink, c_dom, (1.0 - 0.65 * color_mix_w) * c_dom + (0.65 * color_mix_w) * c_sec_col)

    is_new_border = (sdf_blend > -1.5) & (sdf_blend < 2.4)
    border_w = np.clip((2.4 - sdf_blend) / 1.8, 0.0, 1.0) * is_new_border.astype(np.float32)
    for c in range(3):
        out_rgb[:, :, c] = out_rgb[:, :, c] * (1.0 - 0.88 * border_w) + 18.0 * (0.88 * border_w)

    out = np.zeros((CH, CW, 4), dtype=np.uint8)
    out[:, :, :3] = np.clip(out_rgb, 0, 255).astype(np.uint8)
    out[:, :, 3] = out_alpha.astype(np.uint8)
    out[out[:, :, 3] < 12] = [0, 0, 0, 0]
    return out

def draw_4k_overhand_bar_grip(canvas, center_x, top_y, scale=1.0, act_level=0.0, gx_left=LOCKED_LX, gx_right=LOCKED_RX):
    sw, sh = int(round(CW * scale)), int(round(CH * scale))
    paste_x = int(round(center_x - sw / 2))
    paste_y = int(round(top_y))

    pw1, ph1 = int(round(84 * scale)), int(round(68 * scale))
    S4 = 4
    pw4, ph4 = pw1 * S4, ph1 * S4

    r_top = 255
    g_top = int(round(218 - 35 * act_level))
    b_top = int(round(34 - 10 * act_level))
    r_mid = 246
    g_mid = int(round(192 - 42 * act_level))
    b_mid = 20
    r_shd = 215
    g_shd = int(round(138 - 42 * act_level))
    b_shd = 16
    ink = (18, 18, 20, 255)

    for hand_side, gx_1x in [("left", gx_left), ("right", gx_right)]:
        im4 = Image.new("RGBA", (pw4, ph4), (0, 0, 0, 0))
        d4 = ImageDraw.Draw(im4)
        cx4 = pw4 // 2
        cy4 = ph4 // 2
        sc = scale * S4
        in_sign = 1 if hand_side == "left" else -1

        dome_pts = [
            (cx4 - int(17.5 * sc), cy4 - int(4.0 * sc)),
            (cx4 - int(15.0 * sc), cy4 - int(11.5 * sc)),
            (cx4 + int(15.0 * sc), cy4 - int(11.5 * sc)),
            (cx4 + int(17.5 * sc), cy4 - int(4.0 * sc)),
            (cx4 + int(16.0 * sc), cy4 + int(5.0 * sc)),
            (cx4 - int(16.0 * sc), cy4 + int(5.0 * sc)),
        ]
        d4.polygon(dome_pts, fill=(r_mid, g_mid, b_mid, 255), outline=ink)

        thumb_poly = [
            (cx4 + in_sign * int(17.0 * sc), cy4 + int(10.0 * sc)),
            (cx4 + in_sign * int(18.0 * sc), cy4 + int(2.0 * sc)),
            (cx4 + in_sign * int(3.0 * sc),  cy4 + int(1.0 * sc)),
            (cx4 + in_sign * int(1.5 * sc),  cy4 + int(8.5 * sc)),
            (cx4 + in_sign * int(11.5 * sc), cy4 + int(11.5 * sc)),
        ]
        d4.polygon(thumb_poly, fill=(r_mid, g_mid, b_mid, 255), outline=ink)
        for k in range(len(thumb_poly)):
            d4.line([thumb_poly[k], thumb_poly[(k + 1) % len(thumb_poly)]], fill=ink, width=max(3, int(round(2.8 * sc))))

        finger_specs = [
            (-12.6, -9.6,  +6.2, 8.4),
            ( -4.2, -11.4, +7.2, 8.6),
            ( +4.2, -12.2, +7.6, 8.8),
            (+12.6, -11.2, +7.0, 8.6),
        ]

        for f_off, y_top_off, y_bot_off, fw in finger_specs:
            fcx = cx4 + in_sign * int(round(f_off * sc))
            fhw = int(round(0.5 * fw * sc))
            fy0 = cy4 + int(round(y_top_off * sc))
            fy1 = cy4 + int(round(y_bot_off * sc))
            rad = int(round(4.2 * sc))

            d4.rounded_rectangle([fcx - fhw, fy0, fcx + fhw, fy1], radius=rad,
                                 fill=(r_top, g_top, b_top, 255), outline=ink, width=max(3, int(round(2.8 * sc))))
            fy_curl = cy4 + int(round(1.0 * sc))
            if fy1 > fy_curl + 4:
                d4.rounded_rectangle([fcx - fhw + 2, fy_curl, fcx + fhw - 2, fy1 - 2], radius=max(2, rad - 2),
                                     fill=(r_shd, g_shd, b_shd, 255))
            fy_hi = fy0 + int(round(3.5 * sc))
            d4.line([(fcx - fhw + int(3*sc), fy_hi), (fcx + fhw - int(3*sc), fy_hi)],
                    fill=(255, 242, 130, 220), width=max(2, int(round(2.0 * sc))))
            d4.rounded_rectangle([fcx - fhw, fy0, fcx + fhw, fy1], radius=rad,
                                 fill=None, outline=ink, width=max(3, int(round(2.8 * sc))))
            fy_crease = cy4 - int(round(2.2 * sc))
            d4.arc([fcx - fhw + int(2*sc), fy_crease - int(2*sc), fcx + fhw - int(2*sc), fy_crease + int(3*sc)],
                   start=15, end=165, fill=ink, width=max(2, int(round(1.8 * sc))))

        im1 = im4.resize((pw1, ph1), Image.Resampling.LANCZOS)
        hx = int(round(paste_x + gx_1x * scale - pw1 / 2))
        hy = int(round(paste_y + BAR_Y * scale - ph1 / 2))
        canvas.alpha_composite(im1, (hx, hy))

def clean_old_fist_above_wrist(frame_rgba):
    """
    Trims the old raw AI fist above y = 99 (`y < 99`) in the hand columns and copies
    the true wrist row `y = 99` upward to `y = 91..98` (6px behind the thumb & bar)
    so no old thumb sticks out and the real hand-drawn wrist connects 100% seamlessly!
    """
    out = frame_rgba.copy()
    for gx in [int(LOCKED_LX), int(LOCKED_RX)]:
        out[:99, gx - 34 : gx + 34] = [0, 0, 0, 0]
        for y_w in range(91, 99):
            out[y_w, gx - 26 : gx + 26] = out[99, gx - 26 : gx + 26]
    return out

def get_arm_outer_and_inner_edge_at_y(mask, y_coord, side="left", sh_y=200):
    y_c = max(0, min(CH - 1, int(round(y_coord))))
    row_m = (mask[max(0, y_c - 1):min(CH, y_c + 2), :].max(axis=0)) > 0

    if side == "left":
        xs = np.where(row_m[:210])[0]
        if len(xs) == 0:
            return 145.0, 175.0
        x_out = int(xs.min())
        x_in = x_out
        for x in range(x_out, 205):
            if row_m[x]:
                x_in = x
            elif x > x_out + 8:
                break
        return float(x_out), float(max(x_out + 14, min(186, x_in)))
    else:
        xs = np.where(row_m[270:])[0] + 270
        if len(xs) == 0:
            return 305.0, 335.0
        x_out = int(xs.max())
        x_in = x_out
        for x in range(x_out, 275, -1):
            if row_m[x]:
                x_in = x
            elif x < x_out - 8:
                break
        return float(max(294, min(x_out - 14, x_in))), float(x_out)

def get_45_perfect_arm_landmarks(kp_rgba):
    mask = (kp_rgba[:, :, 3] > 128).astype(np.uint8)
    yy, xx = np.mgrid[0:CH, 0:CW]
    r, g, b = kp_rgba[:, :, 0].astype(int), kp_rgba[:, :, 1].astype(int), kp_rgba[:, :, 2].astype(int)

    hy = int(np.where(mask[:, 240] > 0)[0].min())
    fy = int(np.where(mask > 0)[0].max())

    shorts_mask = (mask > 0) & (r < 55) & (g < 55) & (b < 55) & (yy > hy + 120) & (yy < hy + 300) & (np.abs(xx - 240) < 75)
    sys, sxs = np.where(shorts_mask)
    sy = int(np.percentile(sys, 5))
    sy_bot = int(np.percentile(sys, 92))
    sw_left = int(np.percentile(sxs, 3))
    sw_right = int(np.percentile(sxs, 97))

    ky = int(sy_bot + 0.42 * (fy - sy_bot))
    k_xs = np.where(mask[ky, :] > 0)[0]
    kx_left = int(k_xs.min()) if len(k_xs) else 194
    kx_right = int(k_xs.max()) if len(k_xs) else 286

    f_xs = np.where(mask[fy - 18, :] > 0)[0]
    fx_left = int(f_xs.min() + 8) if len(f_xs) else 205
    fx_right = int(f_xs.max() - 8) if len(f_xs) else 275

    l_fist_xs = np.where((mask[76:102, :210] > 0))[1]
    r_fist_xs = np.where((mask[76:102, 270:] > 0))[1] + 270
    lx_fist = int(np.median(l_fist_xs))
    rx_fist = int(np.median(r_fist_xs))

    sh_y = hy + 52
    lx_wr_out, lx_wr_in = get_arm_outer_and_inner_edge_at_y(mask, 104, "left", sh_y)
    rx_wr_in, rx_wr_out = get_arm_outer_and_inner_edge_at_y(mask, 104, "right", sh_y)

    # Use [0.25, 0.50, 0.75] of (sh_y - 104) so all 3 levels lie strictly ABOVE the shoulder junction sh_y!
    arm_span_y = max(48.0, float(sh_y - 104))
    arm_level_pts = []
    for frac_a in [0.25, 0.50, 0.75]:
        y_a = 104.0 + frac_a * arm_span_y
        lx_o, lx_i = get_arm_outer_and_inner_edge_at_y(mask, y_a, "left", sh_y)
        rx_i, rx_o = get_arm_outer_and_inner_edge_at_y(mask, y_a, "right", sh_y)
        arm_level_pts.extend([[lx_o, y_a], [lx_i, y_a], [rx_i, y_a], [rx_o, y_a]])

    y_ap = min(CH - 1, hy + 74)
    ap_xs = np.where(mask[y_ap, 145:335] > 0)[0] + 145
    lx_ap = int(ap_xs.min()) if len(ap_xs) else 174
    rx_ap = int(ap_xs.max()) if len(ap_xs) else 306

    y_lat = min(CH - 1, hy + 118)
    lat_xs = np.where(mask[y_lat, 155:325] > 0)[0] + 155
    lx_lat = int(lat_xs.min()) if len(lat_xs) else 182
    rx_lat = int(lat_xs.max()) if len(lat_xs) else 298

    pts = [
        [0, 0], [CW - 1, 0], [CW - 1, CH - 1], [0, CH - 1],
        [lx_fist - 15, 92], [lx_fist + 15, 92],
        [rx_fist - 15, 92], [rx_fist + 15, 92],
        [lx_wr_out, 104], [lx_wr_in, 104],
        [rx_wr_in, 104], [rx_wr_out, 104],
        *arm_level_pts,
        [lx_ap, y_ap], [rx_ap, y_ap],
        [182, sh_y], [298, sh_y],
        [214, hy + 2], [240, hy], [266, hy + 2],
        [214, hy + 28], [266, hy + 28], [240, hy + 56],
        [lx_lat, y_lat], [240, y_lat], [rx_lat, y_lat],
        [190, sy], [290, sy],
        [sw_left, sy_bot], [sw_right, sy_bot],
        [kx_left, ky], [kx_right, ky],
        [fx_left, fy], [fx_right, fy],
    ]
    return np.array(pts, dtype=np.float32)

pts1_raw = get_45_perfect_arm_landmarks(kp1_raw)
pts2_raw = get_45_perfect_arm_landmarks(kp2_raw)
pts3_raw = get_45_perfect_arm_landmarks(kp3_raw)

for k in range(8, 26):
    print(f"pt {k:02d}: P1={pts1_raw[k].round(1)} | P2={pts2_raw[k].round(1)} | P3={pts3_raw[k].round(1)}")

def render_head_with_natural_gathered_mouth_4k(frame_rgba, hy_f, effort):
    """
    Natural 4K Gathered/Pursed Mouth Progression (`usta se malo skupe pri naporu i izdisaju`):
      - Zero wide teeth grin!
      - Zero white triangle beard over the chin!
      - As effort increases (0.0 -> 1.0):
        1) The resting mouth (half-width 21px in 4x space) progressively GATHERS / NARROWS
           inward (`malo se skupe usta`) to a compact, tight comic effort mouth (half-width 11px in 4x space!).
        2) In the center of the gathered lips, a natural, narrow horizontal-oval parted-lip
           exhale slit (`3:1` width-to-height ratio, with a thicker upper lip arch and a
           pronounced lower-lip pucker shadow crease beneath it) opens subtly as he exhales!
        3) Two subtle inward lip-corner pucker dimples `( — )` frame the gathered mouth,
           paired with furrowed eyebrows and two vertical glabellar frown lines.
    """
    out = frame_rgba.copy()
    y_h0 = max(0, hy_f - 2)
    y_clear0 = max(0, hy_f - 18)
    out[y_clear0 : y_h0 + 46, 214 : 266] = [0, 0, 0, 0]

    mh_h, mh_w, _ = master_head_patch.shape
    S4 = 4
    hw4, hh4 = mh_w * S4, mh_h * S4
    head_4x = cv2.resize(master_head_patch, (hw4, hh4), interpolation=cv2.INTER_LANCZOS4)

    if effort > 0.15:
        r4 = head_4x[:, :, 0].astype(np.float32)
        g4 = head_4x[:, :, 1].astype(np.float32)
        b4 = head_4x[:, :, 2].astype(np.float32)
        a4 = head_4x[:, :, 3].astype(np.float32)
        yy4, xx4 = np.mgrid[0:hh4, 0:hw4].astype(np.float32)
        cx4 = 28.0 * S4 # 112.0
        hy4 = 2.0 * S4  # 8.0

        eye_mask4 = (yy4 >= hy4 + 108) & (yy4 <= hy4 + 140) & (np.abs(xx4 - cx4) <= 68)
        is_yellow4 = (a4 > 200) & ((r4 - b4) > 55) & (~eye_mask4)

        # Cleanly erase the wide resting mouth line (and the small chin crease at y=hy+52 if needed)
        # by sampling the natural golden skin tone around the mouth so we can draw the narrower gathered mouth!
        my4 = int(round(hy4 + 48.5 * S4)) # 202
        mouth_erase_mask = (yy4 >= my4 - 9) & (yy4 <= my4 + 8) & (np.abs(xx4 - cx4) <= 34)
        r4 = np.where(mouth_erase_mask, 240.0, r4)
        g4 = np.where(mouth_erase_mask, 208.0, g4)
        b4 = np.where(mouth_erase_mask, 12.0, b4)

        cheek_flush = (
            np.exp(-(((xx4 - (cx4 - 38.0))/28.0)**2 + ((yy4 - (hy4 + 152.0))/24.0)**2)) +
            np.exp(-(((xx4 - (cx4 + 38.0))/28.0)**2 + ((yy4 - (hy4 + 152.0))/24.0)**2)) +
            0.45 * np.exp(-(((xx4 - cx4)/52.0)**2 + ((yy4 - (hy4 + 72.0))/28.0)**2))
        )
        w_flush = np.where(is_yellow4 | mouth_erase_mask, np.clip(cheek_flush * effort * 0.38, 0.0, 0.36), 0.0)
        head_4x[:, :, 0] = np.clip(r4, 0, 255).astype(np.uint8)
        head_4x[:, :, 1] = np.clip(g4 * (1.0 - 0.55 * w_flush), 0, 255).astype(np.uint8)
        head_4x[:, :, 2] = np.clip(b4 * (1.0 - 0.40 * w_flush) + 10.0 * w_flush, 0, 255).astype(np.uint8)

        pil_h4 = Image.fromarray(head_4x, mode="RGBA")
        d4 = ImageDraw.Draw(pil_h4)

        # 1. Furrowed Eyebrows & Glabellar Frown Lines
        brow_drop = int(round(min(1.0, (effort - 0.15) / 0.65) * 6.0))
        d4.line([(cx4 - 36, hy4 + 109 - brow_drop // 2), (cx4 - 7, hy4 + 116 + brow_drop)], fill=(18, 18, 20, 255), width=5)
        d4.line([(cx4 + 36, hy4 + 109 - brow_drop // 2), (cx4 + 7, hy4 + 116 + brow_drop)], fill=(18, 18, 20, 255), width=5)
        if effort >= 0.30:
            d4.line([(cx4 - 7, hy4 + 97), (cx4 - 5, hy4 + 114)], fill=(18, 18, 20, 235), width=3)
            d4.line([(cx4 + 7, hy4 + 97), (cx4 + 5, hy4 + 114)], fill=(18, 18, 20, 235), width=3)

        # 2. Natural Gathered/Pursed Mouth (`malo se skupe usta`):
        # Notice how the mouth width contracts smoothly from 20px (at effort=0.15) down to 11px (at effort=1.0)!
        u_eff = min(1.0, (effort - 0.15) / 0.75)
        mw = int(round(19.0 - 8.0 * u_eff)) # 19px -> 11px half-width in 4x space (narrowed, gathered lips!)

        if effort < 0.50:
            # Tightly gathered, slightly arched closed lips
            d4.line([(cx4 - mw, my4 + 2), (cx4 - mw // 2, my4 - 1), (cx4 + mw // 2, my4 - 1), (cx4 + mw, my4 + 2)],
                    fill=(18, 18, 20, 255), width=5)
            # Pronounced lower-lip shadow crease (shows the lower lip pushing up & gathering!)
            d4.arc([cx4 - mw + 3, my4 + 2, cx4 + mw - 3, my4 + 9], start=15, end=165, fill=(45, 38, 12, 235), width=3)
            # Subtle inward corner dimples `(   )`
            d4.arc([cx4 - mw - 6, my4 - 6, cx4 - mw + 3, my4 + 7], start=110, end=250, fill=(18, 18, 20, 215), width=3)
            d4.arc([cx4 + mw - 3, my4 - 6, cx4 + mw + 6, my4 + 7], start=-70, end=70, fill=(18, 18, 20, 215), width=3)
        else:
            # Gathered / Pursed Exhale Mouth (`skupljena usta pri izdisaju`):
            # Compact horizontal-oval parted lip slit in the center (`ow = 9px, oh = 3.5px` in 4x space -> 2.6:1 aspect ratio!)
            u_p = min(1.0, (effort - 0.50) / 0.40)
            ow = int(round(8.5 + 1.0 * u_p)) # 9.5px half-width in 4x (compact!)
            oh = int(round(2.5 + 1.5 * u_p)) # 4.0px half-height in 4x (natural narrow parted-lip opening, NOT a round hole!)

            # Subtle warm lip-volume shading around the gathered lips
            d4.ellipse([cx4 - mw - 2, my4 - oh - 4, cx4 + mw + 2, my4 + oh + 5],
                       fill=(224, 184, 18, 255))

            # Gathered lip corners pinching inward into the central opening
            d4.line([(cx4 - mw - 2, my4 + 2), (cx4 - ow + 1, my4)], fill=(18, 18, 20, 255), width=5)
            d4.line([(cx4 + ow - 1, my4), (cx4 + mw + 2, my4 + 2)], fill=(18, 18, 20, 255), width=5)

            # Central compact parted-lip exhale opening
            d4.ellipse([cx4 - ow, my4 - oh, cx4 + ow, my4 + oh],
                       fill=(28, 20, 20, 255), outline=(18, 18, 20, 255), width=4)

            # Strong lower-lip pucker shadow arc right beneath the gathered mouth
            d4.arc([cx4 - ow - 1, my4 + oh, cx4 + ow + 1, my4 + oh + 8], start=10, end=170, fill=(18, 18, 20, 240), width=4)

            # Inward-gathered cheek/lip pucker lines `(  -o-  )`
            d4.arc([cx4 - mw - 8, my4 - 8, cx4 - mw + 2, my4 + 9], start=110, end=250, fill=(18, 18, 20, 235), width=3)
            d4.arc([cx4 + mw - 2, my4 - 8, cx4 + mw + 8, my4 + 9], start=-70, end=70, fill=(18, 18, 20, 235), width=3)

        head_4x = np.array(pil_h4)

    hf = head_4x.astype(np.float32)
    an = hf[:, :, 3:4] / 255.0
    pm = cv2.resize(hf[:, :, :3] * an, (mh_w, mh_h), interpolation=cv2.INTER_AREA)
    al = cv2.resize(hf[:, :, 3], (mh_w, mh_h), interpolation=cv2.INTER_AREA)
    head_1x = np.zeros((mh_h, mh_w, 4), dtype=np.uint8)
    head_1x[:, :, :3] = np.clip(pm / np.maximum(al[:, :, None] / 255.0, 1e-5), 0, 255).astype(np.uint8)
    head_1x[:, :, 3] = np.clip(al, 0, 255).astype(np.uint8)

    roi_h = out[y_h0 : y_h0 + mh_h, 240 - 28 : 240 + 28]
    m_head = head_1x[:, :, 3] > 64
    roi_h[m_head] = head_1x[m_head]
    out[y_h0 : y_h0 + mh_h, 240 - 28 : 240 + 28] = roi_h
    return out

def lock_fists_and_wrists_45(pts, abdominal_crunch_px=0.0):
    out_p = pts.copy()
    dx_l = LOCKED_LX - 0.5 * (pts[4, 0] + pts[5, 0])
    dx_r = LOCKED_RX - 0.5 * (pts[6, 0] + pts[7, 0])
    out_p[4] = [LOCKED_LX - 15.0, 92.0]
    out_p[5] = [LOCKED_LX + 15.0, 92.0]
    out_p[6] = [LOCKED_RX - 15.0, 92.0]
    out_p[7] = [LOCKED_RX + 15.0, 92.0]

    w_wr_l = max(11.0, 0.5 * (pts[9, 0] - pts[8, 0]))
    w_wr_r = max(11.0, 0.5 * (pts[11, 0] - pts[10, 0]))
    out_p[8]  = [LOCKED_LX - w_wr_l, 104.0]
    out_p[9]  = [LOCKED_LX + w_wr_l, 104.0]
    out_p[10] = [LOCKED_RX - w_wr_r, 104.0]
    out_p[11] = [LOCKED_RX + w_wr_r, 104.0]

    # Smooth linear Y-taper across all 3 arm levels (12..23) so the arm tilts straight from shoulder to wrist!
    for level_idx, w_taper in [(12, 0.72), (16, 0.44), (20, 0.18)]:
        out_p[level_idx, 0]     += w_taper * dx_l
        out_p[level_idx + 1, 0] += w_taper * dx_l
        out_p[level_idx + 2, 0] += w_taper * dx_r
        out_p[level_idx + 3, 0] += w_taper * dx_r

    hy = out_p[29, 1]
    orig_sy = out_p[37, 1]
    target_sy = hy + 179.0 - abdominal_crunch_px
    dy_lower = target_sy - orig_sy
    for idx in range(37, 45):
        out_p[idx, 1] += dy_lower
    out_p[37, 0], out_p[38, 0] = 190.0, 290.0
    out_p[39, 0], out_p[40, 0] = 186.0, 294.0
    return out_p

pts1 = lock_fists_and_wrists_45(pts1_raw, 0.0)
pts2 = lock_fists_and_wrists_45(pts2_raw, 4.0)
pts3 = lock_fists_and_wrists_45(pts3_raw, 9.0)

# Keep KP3 and KP4 upper arms full and un-squashed
for idx in range(16, 26):
    pts3[idx, 1] += 10.0

pts4 = pts3.copy()
for idx in range(16, 45):
    pts4[idx, 1] -= 14.0
pts4[24, 1] += 6.0
pts4[25, 1] += 6.0
for idx in range(12, 16):
    pts4[idx, 1] -= 5.0
for idx in range(37, 45):
    pts4[idx, 1] -= 2.0
for idx in range(41, 45):
    pts4[idx, 1] -= 5.0

tri = Delaunay(pts2)
triangles = tri.simplices
kp1 = warp_piecewise_affine(kp1_raw, pts1_raw, pts1, triangles)
kp2 = warp_piecewise_affine(kp2_raw, pts2_raw, pts2, triangles)
kp3 = warp_piecewise_affine(kp3_raw, pts3_raw, pts3, triangles)
kp4 = warp_piecewise_affine(kp3_raw, pts3_raw, pts4, triangles)

def draw_rounded_badge(draw, xy, bg_color, border_color=(18, 18, 18, 255), radius=14, border_w=4, shadow_offset=5):
    x0, y0, x1, y1 = xy
    if shadow_offset > 0:
        draw.rounded_rectangle([x0 + shadow_offset, y0 + shadow_offset, x1 + shadow_offset, y1 + shadow_offset],
                               radius=radius, fill=(18, 18, 18, 225))
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=bg_color, outline=border_color, width=border_w)

def draw_callout_pointer(draw, start_pt, elbow_pt, end_pt, label_title, label_sub, accent_color=(230, 55, 35, 255)):
    sx, sy = int(round(start_pt[0])), int(round(start_pt[1]))
    ex, ey = int(round(elbow_pt[0])), int(round(elbow_pt[1]))
    tx, ty = int(round(end_pt[0])), int(round(end_pt[1]))
    draw.line([(sx, sy), (ex, ey), (tx, ty)], fill=(18, 18, 18, 255), width=7)
    draw.line([(sx, sy), (ex, ey), (tx, ty)], fill=accent_color, width=3)
    draw.ellipse([sx - 8, sy - 8, sx + 8, sy + 8], fill=accent_color, outline=(18, 18, 18, 255), width=3)

    f_title = get_font(FONT_BOLD, 21)
    f_sub = get_font(FONT_REG, 16)
    w_t = draw.textlength(label_title, font=f_title)
    w_s = draw.textlength(label_sub, font=f_sub)
    bw = max(430, int(max(w_t, w_s)) + 52)
    bh = 76
    bx0 = min(tx, W - bw - 35)
    by0 = ty - bh // 2
    draw_rounded_badge(draw, [bx0, by0, bx0 + bw, by0 + bh], (255, 255, 255, 252), (18, 18, 18, 255), radius=12, border_w=4, shadow_offset=4)
    draw.rounded_rectangle([bx0 + 10, by0 + 12, bx0 + 20, by0 + bh - 12], radius=4, fill=accent_color)
    draw.text((bx0 + 30, by0 + 12), label_title, font=f_title, fill=(18, 18, 18, 255))
    draw.text((bx0 + 30, by0 + 43), label_sub, font=f_sub, fill=(70, 70, 70, 255))

def draw_gear(draw, cx, cy, r_outer, r_inner, n_teeth, angle_rad, fill_col, outline_col=(18, 18, 18, 255)):
    pts = []
    for i in range(n_teeth * 4):
        a = angle_rad + (i * math.pi * 2) / (n_teeth * 4)
        r = r_outer if (i % 4 in (1, 2)) else r_inner
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    draw.polygon(pts, fill=fill_col, outline=outline_col)
    for i in range(len(pts)):
        draw.line([pts[i], pts[(i + 1) % len(pts)]], fill=outline_col, width=4)
    draw.ellipse([cx - r_inner * 0.42, cy - r_inner * 0.42, cx + r_inner * 0.42, cy + r_inner * 0.42],
                 fill=(247, 245, 239, 255), outline=outline_col, width=4)

def get_cycle_state(t_sec, cycle_period=2.4):
    u = (t_sec % cycle_period) / cycle_period
    idx = int(round(u * 24)) % 24
    dist_from_peak = abs(idx - 12) / 12.0
    activation = max(0.0, min(1.0, 1.0 - dist_from_peak))
    return idx, activation, 1.0, u

# Enhance KP4 pectoral/lat warmth
r4, g4, b4, a4 = kp4[:,:,0].astype(np.float32), kp4[:,:,1].astype(np.float32), kp4[:,:,2].astype(np.float32), kp4[:,:,3].astype(np.float32)
yy1, xx1 = np.mgrid[0:CH, 0:CW].astype(np.float32)
hy4 = pts4[29, 1]
is_warm4 = (a4 > 180) & ((r4 - b4) > 55) & (r4 > 125) & (g4 > 65)
pec_heat = (
    np.exp(-(((xx1 - 210.0)/42.0)**2 + ((yy1 - (hy4 + 92.0))/42.0)**2)) +
    np.exp(-(((xx1 - 270.0)/42.0)**2 + ((yy1 - (hy4 + 92.0))/42.0)**2))
)
w_p4 = np.where(is_warm4, np.clip(pec_heat * 0.80, 0.0, 0.80), 0.0)
kp4[:, :, 1] = np.clip(g4 * (1.0 - 0.65 * w_p4), 0, 255).astype(np.uint8)
kp4[:, :, 2] = np.clip(b4 * (1.0 - 0.50 * w_p4) + 12.0 * w_p4, 0, 255).astype(np.uint8)

key_imgs = [kp1, kp2, kp3, kp4]
key_pts  = [pts1, pts2, pts3, pts4]

schedule_24 = [
    (0, 0, 0.00),
    (0, 1, 0.25),
    (0, 1, 0.50),
    (0, 1, 0.75),
    (1, 1, 0.00),
    (1, 2, 0.25),
    (1, 2, 0.50),
    (1, 2, 0.75),
    (2, 2, 0.00),
    (2, 3, 0.33),
    (2, 3, 0.67),
    (3, 3, 0.00),
    (3, 3, 0.00),
    (3, 2, 0.25),
    (3, 2, 0.50),
    (3, 2, 0.75),
    (2, 2, 0.00),
    (2, 1, 0.25),
    (2, 1, 0.50),
    (2, 1, 0.75),
    (1, 1, 0.00),
    (1, 0, 0.33),
    (1, 0, 0.67),
    (0, 0, 0.00),
]

v15_body_frames = []
v15_act_levels = []
landmarks_per_frame = []

for i, (idxA, idxB, alpha) in enumerate(schedule_24):
    dist_from_peak = abs(i - 11.5) / 11.5
    core_act = max(0.0, min(1.0, 1.0 - dist_from_peak))
    v15_act_levels.append(core_act)

    if idxA == idxB or alpha == 0.0:
        pts_t = key_pts[idxA].copy()
        hy_f = int(round(pts_t[29, 1]))
        sy_f = int(round(pts_t[37, 1]))
        base_rgba = key_imgs[idxA].copy()
    else:
        ptsA = key_pts[idxA]
        ptsB = key_pts[idxB]
        pts_t = (1.0 - alpha) * ptsA + alpha * ptsB
        hy_f = int(round(pts_t[29, 1]))
        sy_f = int(round(pts_t[37, 1]))
        wA = warp_piecewise_affine(key_imgs[idxA], ptsA, pts_t, triangles)
        wB = warp_piecewise_affine(key_imgs[idxB], ptsB, pts_t, triangles)
        base_rgba = blend_sdf_zero_double_lines(wA, wB, alpha)

    frame_rgba = enhance_abs_and_core_contraction(base_rgba, hy_f, sy_f, core_act)
    frame_rgba = render_head_with_natural_gathered_mouth_4k(frame_rgba, hy_f, effort=core_act)
    frame_rgba = clean_old_fist_above_wrist(frame_rgba)

    Image.fromarray(frame_rgba).save(os.path.join(FRAMES_V15_DIR, f"body_{i:02d}.png"))
    v15_body_frames.append(frame_rgba)

    landmarks_per_frame.append({
        "head_top": hy_f,
        "mouth": (268, hy_f + 48),
        "right_grip": (int(round(LOCKED_RX + 18)), BAR_Y),
        "right_elbow": (int(round(pts_t[19, 0])), int(round(pts_t[19, 1]))),
        "right_bicep": (int(round(pts_t[23, 0])), int(round(pts_t[23, 1]))),
        "right_lat": (int(round(pts_t[36, 0] - 6)), int(round(pts_t[36, 1]))),
        "right_abs": (256, int(round(0.5 * (hy_f + 112 + sy_f)))),
        "right_knee": (int(round(pts_t[42, 0] - 12)), int(round(pts_t[42, 1]))),
    })

def compose_character_v15(canvas, char_idx, center_x, top_y, scale=1.0, show_aura=False, aura_strength=0.0, bar_half_width=340):
    body_im = Image.fromarray(v15_body_frames[char_idx])
    act_lvl = v15_act_levels[char_idx]
    sw, sh = int(round(CW * scale)), int(round(CH * scale))
    body_scaled = body_im.resize((sw, sh), Image.Resampling.LANCZOS)

    paste_x = int(round(center_x - sw / 2))
    paste_y = int(round(top_y))
    bar_y = int(round(paste_y + BAR_Y * scale))
    bar_h = int(max(7, round(8.0 * scale)))

    if show_aura and aura_strength > 0.05:
        alpha_np = np.array(body_scaled)[:, :, 3]
        kernel_sz = int(max(15, round(27 * scale))) | 1
        dilated = cv2.dilate(alpha_np, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_sz, kernel_sz)))
        blurred = cv2.GaussianBlur(dilated, (kernel_sz, kernel_sz), 0)
        aura_rgba = np.zeros((sh, sw, 4), dtype=np.uint8)
        aura_rgba[:, :, 0] = 255
        aura_rgba[:, :, 1] = 80
        aura_rgba[:, :, 2] = 25
        aura_rgba[:, :, 3] = np.clip(blurred.astype(np.float32) * 0.42 * aura_strength, 0, 155).astype(np.uint8)
        canvas.alpha_composite(Image.fromarray(aura_rgba, mode="RGBA"), (paste_x, paste_y))

    body_np = np.array(body_scaled).astype(np.float32)
    by_local = int(round(BAR_Y * scale))
    bh_local = bar_h
    yy_l, xx_l = np.mgrid[0:sh, 0:sw]
    dist_from_bar = np.abs(yy_l - (by_local + int(4 * scale)))
    in_head_neck_x = np.abs(xx_l - (sw / 2.0)) < (36.0 * scale)
    in_shadow_band = in_head_neck_x & (yy_l >= by_local - bh_local - int(4 * scale)) & (yy_l <= by_local + bh_local + int(16 * scale))
    shadow_mask = in_shadow_band & (body_np[:, :, 3] > 100)
    shadow_falloff = np.exp(- (dist_from_bar / (10.0 * scale)) ** 2)
    darken = np.where(shadow_mask, 1.0 - 0.40 * shadow_falloff, 1.0)
    for c in range(3):
        body_np[:, :, c] = np.clip(body_np[:, :, c] * darken, 0, 255)

    canvas.alpha_composite(Image.fromarray(body_np.astype(np.uint8), mode="RGBA"), (paste_x, paste_y))

    draw = ImageDraw.Draw(canvas)
    post_left = center_x - bar_half_width
    post_right = center_x + bar_half_width
    draw.rounded_rectangle([post_left, bar_y - bar_h, post_right, bar_y + bar_h],
                           radius=bar_h, fill=(82, 88, 96, 255), outline=(15, 15, 15, 255), width=4)
    draw.line([(post_left + 10, bar_y - bar_h + 4), (post_right - 10, bar_y - bar_h + 4)],
              fill=(200, 208, 220, 255), width=2)
    draw.line([(post_left + 10, bar_y + bar_h - 4), (post_right - 10, bar_y + bar_h - 4)],
              fill=(48, 52, 58, 255), width=2)
    for px in [post_left, post_right]:
        draw.rounded_rectangle([px - 10, bar_y - 18, px + 10, bar_y + 18],
                               radius=5, fill=(45, 48, 54, 255), outline=(15, 15, 15, 255), width=4)

    draw_4k_overhand_bar_grip(canvas, center_x=center_x, top_y=top_y, scale=scale, act_level=act_lvl, gx_left=LOCKED_LX, gx_right=LOCKED_RX)

    def map_pt(pt):
        return (paste_x + pt[0] * scale, paste_y + pt[1] * scale)

    return map_pt

# 1. Save 24-frame grid: yellow_dude_24_frames_flawless_v15.png
cols, rows = 6, 4
cw, ch = CW, CH
grid_out_img = Image.new("RGB", (cols * cw, rows * ch), (245, 245, 242))
font_grid = get_font(FONT_BOLD, 22)

for i in range(24):
    r_idx = i // cols
    c_idx = i % cols
    x0, y0 = c_idx * cw, r_idx * ch
    cell = Image.new("RGBA", (cw, ch), (245, 245, 242, 255))
    compose_character_v15(cell, i, center_x=cw // 2, top_y=0, scale=1.0, show_aura=False, aura_strength=0.0, bar_half_width=220)
    cdraw = ImageDraw.Draw(cell)
    cdraw.text((16, 14), f"F{i+1:02d}/24", fill=(20, 20, 20, 255), font=font_grid)
    grid_out_img.paste(cell.convert("RGB"), (x0, y0))

grid_v15_path = os.path.join(OUT_DIR, "yellow_dude_24_frames_flawless_v15.png")
grid_out_img.save(grid_v15_path)
print("Saved v15 Flawless 24-frame grid to:", grid_v15_path)

# 2. Save Before vs After comparison against user's `image_772201.jpg` and `image_77227a.jpg`!
if os.path.exists(USER_IMG_2):
    u2_im = Image.open(USER_IMG_2).convert("RGB")
    uw2, uh2 = u2_im.size
    # Render F02 (`char_idx = 1`) at matching zoom to compare directly against `image_77227a.jpg`!
    full_f02 = Image.new("RGBA", (CW, CH), (247, 245, 239, 255))
    f02_draw = ImageDraw.Draw(full_f02)
    for gx in range(0, CW, 42):
        f02_draw.line([(gx, 0), (gx, CH)], fill=(234, 231, 223, 255), width=1)
    for gy in range(0, CH, 42):
        f02_draw.line([(0, gy), (CW, gy)], fill=(234, 231, 223, 255), width=1)
    compose_character_v15(full_f02, 1, center_x=CW // 2, top_y=0, scale=1.0, show_aura=True, aura_strength=0.25, bar_half_width=220)
    after_u2 = full_f02.crop((102, 68, 378, 276)).resize((uw2, uh2), Image.Resampling.LANCZOS).convert("RGB")

    comp_u2 = Image.new("RGB", (uw2 * 2 + 40, uh2 + 80), (245, 245, 242))
    cd_u2 = ImageDraw.Draw(comp_u2)
    cd_u2.text((15, 18), "PRIJE (v14): Šiljak/artifakt i izbočina na podlaktici", font=get_font(FONT_BOLD, 18), fill=(200, 35, 25))
    cd_u2.text((uw2 + 30, 18), "SADA (v15 4K): 0% artifakata + prirodna kontura ruke", font=get_font(FONT_BOLD, 18), fill=(25, 145, 75))
    comp_u2.paste(u2_im, (10, 60))
    comp_u2.paste(after_u2, (uw2 + 30, 60))
    comp_u2_path = os.path.join(OUT_DIR, "red_arrows_arm_and_mouth_fixed_v15.png")
    comp_u2.save(comp_u2_path)
    print("Saved Before vs After arm & artifact comparison to:", comp_u2_path)
else:
    print("No YD_REF_IMG_2 given, skipping before/after comparison")

# 3. Render full 30-second video: yellow_dude_flawless_4k_v15.mp4
W, H = 1920, 1080
bg_base = Image.new("RGBA", (W, H), (247, 245, 239, 255))
bg_draw = ImageDraw.Draw(bg_base)
for gx in range(0, W, 60):
    bg_draw.line([(gx, 0), (gx, H)], fill=(234, 231, 223, 255), width=1)
for gy in range(0, H, 60):
    bg_draw.line([(0, gy), (W, gy)], fill=(234, 231, 223, 255), width=1)

def render_video_frame(frame_idx, total_frames=900, fps=30.0):
    t = frame_idx / fps
    canvas = bg_base.copy()
    draw = ImageDraw.Draw(canvas)

    draw_rounded_badge(draw, [50, 26, 1080, 100], (255, 212, 42, 255), (18, 18, 18, 255), radius=14, border_w=4, shadow_offset=5)
    draw.text((74, 36), "YELLOW DUDE // 4K FLAWLESS ANATOMIJA + SKUPLJENA USTA (V15)", font=get_font(FONT_BOLD, 25), fill=(18, 18, 18, 255))
    draw.text((74, 71), "0% ARTIFAKATA NA RUKAMA • PRIRODNO SKUPLJENA USTA PRI NAPORU • 4K NADHVAT", font=get_font(FONT_MONO, 16), fill=(45, 45, 45, 255))

    if t < 7.0:
        idx, act, bounce, u = get_cycle_state(t, cycle_period=2.333)
        rep_num = int(t / 2.333) + 1
        lm = landmarks_per_frame[idx]

        map_pt = compose_character_v15(
            canvas, idx, center_x=960, top_y=118, scale=1.02,
            show_aura=True, aura_strength=act, bar_half_width=360
        )

        draw_rounded_badge(draw, [50, 155, 560, 455], (255, 255, 255, 250), radius=16)
        draw.text((78, 178), "FAZA POKRETA (24-FRAME LOOP)", font=get_font(FONT_BOLD, 21), fill=(18, 18, 18, 255))
        phase_name = (
            "1. PASIVNI VIS (MIRNA USTA & PRAVE RUKE)" if idx in (0, 1, 22, 23) else
            "2. POČETAK VUČENJA (STISNUTE USNE)" if idx in (2, 3, 4, 20, 21) else
            "3. SREDNJI ZGIB (SKUPLJENA USTA)" if idx in (5, 6, 7, 8, 9) else
            "4. VRHUNAC (SKUPLJENA USTA U IZDISAJU)" if idx in (10, 11, 12, 13, 14) else
            "5. KONTROLISANI SPUST"
        )
        draw.rounded_rectangle([78, 218, 532, 266], radius=8, fill=(255, 212, 42, 255), outline=(18, 18, 18, 255), width=3)
        draw.text((90, 232), phase_name, font=get_font(FONT_BOLD, 16), fill=(18, 18, 18, 255))

        draw.text((78, 288), f"AKTIVNI FREJM: F{idx+1:02d} / 24", font=get_font(FONT_MONO, 20), fill=(30, 30, 30, 255))
        draw.text((78, 324), f"PONAVLJANJE (REP): #{rep_num}  |  TEMPO: 2-1-2", font=get_font(FONT_MONO, 18), fill=(80, 80, 80, 255))

        draw.text((78, 368), f"MIŠIĆNA AKTIVACIJA & NAPOR: {int(round(act * 100))}%", font=get_font(FONT_BOLD, 17), fill=(18, 18, 18, 255))
        draw.rounded_rectangle([78, 398, 532, 426], radius=8, fill=(230, 230, 230, 255), outline=(18, 18, 18, 255), width=3)
        fill_w = int(max(14, 454 * act))
        bar_col = (230, 55, 35, 255) if act > 0.5 else (255, 165, 30, 255)
        draw.rounded_rectangle([78, 398, 78 + fill_w, 426], radius=8, fill=bar_col, outline=(18, 18, 18, 255), width=3)

        draw_callout_pointer(
            draw,
            start_pt=map_pt(lm["right_grip"]),
            elbow_pt=(1260, 190),
            end_pt=(1340, 190),
            label_title="4K ANATOMSKI NADHVAT (OVERHAND GRIP)",
            label_sub="Prirodan spoj zgloba šake i 4 prsta oko čelične šipke",
            accent_color=(255, 145, 20, 255)
        )
        draw_callout_pointer(
            draw,
            start_pt=map_pt(lm["right_bicep"]),
            elbow_pt=(1260, 340),
            end_pt=(1340, 340),
            label_title="ČISTA KONTURA RUKU (0% ARTIFAKATA)",
            label_sub="Praćenje vanjske i unutrašnje ivice ruke na 3 nivoa",
            accent_color=(230, 55, 35, 255)
        )
        draw_callout_pointer(
            draw,
            start_pt=map_pt(lm["mouth"]),
            elbow_pt=(1260, 500),
            end_pt=(1340, 500),
            label_title="PRIRODNO SKUPLJENA USTA PRI NAPORU",
            label_sub="Usne se postepeno skupe u naporu i izdisaju na vrhu",
            accent_color=(35, 155, 85, 255)
        )

    elif t < 15.0:
        idx, act, bounce, u = get_cycle_state(t, cycle_period=2.40)
        lm = landmarks_per_frame[idx]

        map_pt = compose_character_v15(
            canvas, idx, center_x=960, top_y=115, scale=1.03,
            show_aura=True, aura_strength=max(0.35, act), bar_half_width=365
        )

        draw_rounded_badge(draw, [50, 150, 555, 555], (255, 255, 255, 250), radius=16)
        draw.text((78, 175), "X-RAY MIŠIĆNA HIPERTROFIJA", font=get_font(FONT_BOLD, 24), fill=(215, 40, 30, 255))
        draw.text((78, 210), "Prirodna anatomija ruku, leđa, trbušnjaka i nogu:", font=get_font(FONT_REG, 18), fill=(60, 60, 60, 255))

        muscles = [
            ("BICEPS BRACHII & BRACHIORADIALIS", min(100, int(round(35 + 65 * act))), (240, 95, 25, 255)),
            ("TRICEPS LONG HEAD & DELTOID", min(100, int(round(30 + 70 * act))), (225, 45, 35, 255)),
            ("LATISSIMUS DORSI (Glatka V-kontura)", min(100, int(round(35 + 65 * act))), (215, 55, 45, 255)),
            ("RECTUS ABDOMINIS (6-Pack Core Crunch)", min(100, int(round(30 + 70 * act))), (235, 75, 20, 255)),
            ("ORB. ORIS & CORE BRACING (Skupljena usta)", min(100, int(round(40 + 60 * act))), (40, 145, 90, 255)),
        ]
        my = 253
        for m_name, m_pct, m_col in muscles:
            draw.text((78, my), f"{m_name}: {m_pct}%", font=get_font(FONT_BOLD, 16), fill=(20, 20, 20, 255))
            draw.rounded_rectangle([78, my + 24, 525, my + 44], radius=6, fill=(232, 232, 232, 255), outline=(18, 18, 18, 255), width=2)
            fw = int(max(12, 447 * (m_pct / 100.0)))
            draw.rounded_rectangle([78, my + 24, 78 + fw, my + 44], radius=6, fill=m_col, outline=(18, 18, 18, 255), width=2)
            my += 58

        draw_callout_pointer(
            draw,
            start_pt=map_pt(lm["mouth"]),
            elbow_pt=(1275, 200),
            end_pt=(1340, 200),
            label_title="PRIRODAN IZRAZ LICA (SKUPLJENA USTA)",
            label_sub="Namrštene obrve i skupljene usne u kontrolisanom izdisaju",
            accent_color=(240, 95, 25, 255)
        )
        draw_callout_pointer(
            draw,
            start_pt=map_pt(lm["right_bicep"]),
            elbow_pt=(1275, 360),
            end_pt=(1340, 360),
            label_title="GLATKA UNUTRAŠNJA I VANJSKA IVICA RUKE",
            label_sub="0% šiljaka ili izbočina na podlaktici u svim međufrejmovima",
            accent_color=(225, 45, 35, 255)
        )
        draw_callout_pointer(
            draw,
            start_pt=map_pt(lm["right_knee"]),
            elbow_pt=(1275, 530),
            end_pt=(1340, 530),
            label_title="HOLLOW-BODY SAVIJANJE NOGU & ABS",
            label_sub="Noge i trbušnjaci rade sinhronizovano kroz cijeli pokret",
            accent_color=(35, 155, 85, 255)
        )

    elif t < 23.0:
        idx, act, bounce, u = get_cycle_state(t, cycle_period=2.40)
        lm = landmarks_per_frame[idx]

        map_pt = compose_character_v15(
            canvas, idx, center_x=960, top_y=115, scale=1.03,
            show_aura=True, aura_strength=act, bar_half_width=365
        )

        draw_rounded_badge(draw, [50, 155, 555, 605], (255, 255, 255, 250), radius=16)
        draw.text((78, 180), "MEHANIČKI OBRTNI MOMENT", font=get_font(FONT_BOLD, 24), fill=(18, 18, 18, 255))
        draw.text((78, 215), "Čista biomehanika od F01 do F24:", font=get_font(FONT_REG, 18), fill=(70, 70, 70, 255))

        angle = u * math.pi * 2
        draw_gear(draw, 215, 360, 76, 58, 10, angle, (255, 212, 42, 255))
        draw_gear(draw, 358, 410, 56, 42, 8, -angle * 1.25 + 0.3, (230, 65, 40, 255))

        elbow_deg = int(round(176 - 118 * act))
        hip_deg = int(round(180 - 22 * act))
        draw.text((78, 500), f"UGAO U LAKTU: {elbow_deg}°  |  KUK/KOLJENO: {hip_deg}°", font=get_font(FONT_MONO, 19), fill=(18, 18, 18, 255))
        draw.text((78, 538), f"AKTIVACIJA & NAPOR: {int(round(35 + 65*act))}%", font=get_font(FONT_MONO, 20), fill=(215, 45, 30, 255))

        draw_callout_pointer(
            draw,
            start_pt=map_pt(lm["right_elbow"]),
            elbow_pt=(1275, 280),
            end_pt=(1340, 280),
            label_title=f"PRIRODNA FLEKSIJA LAKTA: {elbow_deg}°",
            label_sub="3 prave anatomske poze (180° → 110° → 60°) bez artifakata",
            accent_color=(255, 145, 20, 255)
        )
        draw_callout_pointer(
            draw,
            start_pt=map_pt(lm["mouth"]),
            elbow_pt=(1275, 450),
            end_pt=(1340, 450),
            label_title="SKUPLJENA USTA PRI IZDISAJU",
            label_sub="Prirodno skupljanje usana umjesto puhanja kroz zube",
            accent_color=(230, 55, 35, 255)
        )

    else:
        idx, act, bounce, u = get_cycle_state(t, cycle_period=2.333)

        draw_rounded_badge(draw, [65, 122, 915, 968], (255, 255, 255, 238), radius=18)
        draw_rounded_badge(draw, [1005, 122, 1855, 968], (255, 255, 255, 238), radius=18)

        draw_rounded_badge(draw, [105, 142, 875, 206], (235, 235, 235, 255), radius=12, shadow_offset=3)
        draw.text((135, 159), "A) PASIVNI VIS (MIRNA USTA • 0% ARTIFAKATA NA RUKAMA)", font=get_font(FONT_BOLD, 19), fill=(70, 70, 70, 255))

        draw_rounded_badge(draw, [1045, 142, 1815, 206], (255, 212, 42, 255), radius=12, shadow_offset=3)
        draw.text((1075, 159), "B) PUNI ZGIB (SKUPLJENA USTA • 4K NADHVAT • AKTIVNI ABS)", font=get_font(FONT_BOLD, 17), fill=(18, 18, 18, 255))

        comp_scale = 0.82
        left_idx = 0 if int(t * 2) % 2 == 0 else 1
        compose_character_v15(
            canvas, left_idx, center_x=490, top_y=222, scale=comp_scale,
            show_aura=False, aura_strength=0.0, bar_half_width=290
        )
        compose_character_v15(
            canvas, idx, center_x=1430, top_y=222, scale=comp_scale,
            show_aura=True, aura_strength=act, bar_half_width=290
        )

        draw_rounded_badge(draw, [100, 880, 880, 950], (248, 248, 248, 255), radius=10, border_w=3, shadow_offset=2)
        draw.text((120, 892), "• 0% šiljaka i izbočina na unutrašnjoj strani podlaktica (F01-F24)", font=get_font(FONT_BOLD, 17), fill=(80, 80, 80, 255))
        draw.text((120, 918), "• 4K anatomski nadhvat oko šipke • Mirna, opuštena usta u visu", font=get_font(FONT_REG, 16), fill=(110, 110, 110, 255))

        draw_rounded_badge(draw, [1040, 880, 1820, 950], (255, 244, 215, 255), radius=10, border_w=3, shadow_offset=2)
        draw.text((1060, 892), f"• Frejm F{idx+1:02d}/24 • Prirodno skupljena usta pri usponu • Napor: {int(round(act*100))}%", font=get_font(FONT_BOLD, 17), fill=(200, 40, 25, 255))
        draw.text((1060, 918), "• Aktivni trbušnjaci i prirodno savijanje nogu u Hollow-Body položaju", font=get_font(FONT_REG, 16), fill=(40, 40, 40, 255))

    draw_rounded_badge(draw, [50, 995, 1870, 1052], (18, 18, 18, 255), (18, 18, 18, 255), radius=12, border_w=2, shadow_offset=0)
    prog_w = int(round(1800 * (frame_idx / float(total_frames - 1))))
    draw.rounded_rectangle([60, 1005, 60 + max(16, prog_w), 1042], radius=8, fill=(255, 212, 42, 255))
    scene_label = (
        "SCENA 1/4: 24-FRAME FLAWLESS ARMS & GATHERED MOUTH" if t < 7.0 else
        "SCENA 2/4: X-RAY HIPERTROFIJA & SKUPLJENA USTA" if t < 15.0 else
        "SCENA 3/4: MEHANIČKI MOMENT & BIOMEHANIKA" if t < 23.0 else
        "SCENA 4/4: KOMPARACIJA (PASIVNI VIS vs. PUNI ZGIB)"
    )
    draw.text((80, 1012), f"{scene_label}   |   {t:05.2f}s / 30.00s   |   FRAME {frame_idx+1:03d}/900", font=get_font(FONT_MONO, 18), fill=(18, 18, 18, 255) if prog_w > 650 else (255, 255, 255, 255))

    return canvas.convert("RGB")

OUT_MP4_V15 = os.path.join(OUT_DIR, "yellow_dude_flawless_4k_v15.mp4")
cmd = [
    "ffmpeg", "-y",
    "-f", "rawvideo",
    "-vcodec", "rawvideo",
    "-s", f"{W}x{H}",
    "-pix_fmt", "rgb24",
    "-r", "30",
    "-i", "-",
] + (["-i", AUDIO_WAV] if os.path.exists(AUDIO_WAV) else []) + [
    "-c:v", "libx264",
    "-threads", "2",
    "-preset", "ultrafast",
    "-crf", "17",
    "-pix_fmt", "yuv420p",
] + (["-c:a", "aac", "-b:a", "192k", "-shortest"] if os.path.exists(AUDIO_WAV) else []) + [
    OUT_MP4_V15
]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
for f_idx in range(900):
    frame_rgb = render_video_frame(f_idx)
    proc.stdin.write(frame_rgb.tobytes())
    if (f_idx + 1) % 150 == 0:
        print(f"Rendered {f_idx + 1}/900 frames...")
proc.stdin.close()
stderr_out = proc.stderr.read().decode("utf-8", errors="ignore")
proc.wait()
print("FFmpeg return code:", proc.returncode, "Size:", os.path.getsize(OUT_MP4_V15))
