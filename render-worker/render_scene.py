import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

FT = 0.3048


def argv_after_double_dash():
    argv = sys.argv
    if "--" not in argv:
        raise RuntimeError("Missing worker arguments")
    return argv[argv.index("--") + 1 :]


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def material(name, base, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def cube(name, location, dimensions, mat, bevel=0.025):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat:
        obj.data.materials.append(mat)
    if bevel > 0:
        mod = obj.modifiers.new(name="Soft edges", type="BEVEL")
        mod.width = bevel
        mod.segments = 3
    return obj


def cylinder(name, location, radius, depth, mat, rotation=(0, 0, 0), vertices=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    return obj


def look_at(obj, point):
    direction = Vector(point) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def add_area(name, location, energy, size, target):
    data = bpy.data.lights.new(name=name, type="AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    look_at(obj, target)
    return obj


def add_room(room, origin, mats):
    ox, oy = origin
    width = float(room.get("width", 12)) * FT
    depth = float(room.get("depth", 12)) * FT
    height = float(room.get("height", 8)) * FT
    wall_t = 0.10
    floor_t = 0.08

    floor = cube(
        f"{room.get('name', 'Room')}_FLOOR",
        (ox + width / 2, oy + depth / 2, floor_t / 2),
        (width, depth, floor_t),
        mats["floor"],
        bevel=0.015,
    )
    floor["field_verified"] = bool(room.get("verified"))

    cube(
        f"{room.get('name', 'Room')}_BACK_WALL",
        (ox + width / 2, oy + depth - wall_t / 2, height / 2),
        (width, wall_t, height),
        mats["wall"],
    )
    cube(
        f"{room.get('name', 'Room')}_LEFT_WALL",
        (ox + wall_t / 2, oy + depth / 2, height / 2),
        (wall_t, depth, height),
        mats["wall"],
    )
    cube(
        f"{room.get('name', 'Room')}_RIGHT_WALL",
        (ox + width - wall_t / 2, oy + depth / 2, height / 2),
        (wall_t, depth, height),
        mats["wall"],
    )

    trim_h = 0.075
    cube("BASE_TRIM_BACK", (ox + width / 2, oy + depth - 0.055, trim_h / 2 + floor_t), (width, 0.055, trim_h), mats["trim"], bevel=0.01)
    cube("BASE_TRIM_LEFT", (ox + 0.055, oy + depth / 2, trim_h / 2 + floor_t), (0.055, depth, trim_h), mats["trim"], bevel=0.01)
    cube("BASE_TRIM_RIGHT", (ox + width - 0.055, oy + depth / 2, trim_h / 2 + floor_t), (0.055, depth, trim_h), mats["trim"], bevel=0.01)

    return {"origin": (ox, oy), "width": width, "depth": depth, "height": height}


def add_mini_split(room_geo, mats):
    ox, oy = room_geo["origin"]
    width = room_geo["width"]
    depth = room_geo["depth"]
    height = room_geo["height"]
    body_w, body_d, body_h = 1.05, 0.22, 0.30
    x = ox + width / 2
    y = oy + depth - 0.18
    z = max(1.6, height - 0.52)
    cube("HVAC_MINISPLIT_BODY", (x, y, z), (body_w, body_d, body_h), mats["equipment"], bevel=0.05)
    cube("HVAC_MINISPLIT_VENT", (x, y - body_d / 2 - 0.012, z - 0.065), (body_w * 0.83, 0.025, 0.055), mats["dark"], bevel=0.008)
    cube("HVAC_MINISPLIT_DISPLAY", (x + body_w * 0.29, y - body_d / 2 - 0.014, z + 0.03), (0.11, 0.018, 0.025), mats["display"], bevel=0.004)


def add_rtu(anchor, mats):
    x, y = anchor
    body = cube("HVAC_RTU_BODY", (x, y, 0.58), (2.25, 1.45, 1.05), mats["metal"], bevel=0.055)
    body["equipment_type"] = "generic packaged rooftop unit"
    cube("HVAC_RTU_BASE", (x, y, 0.10), (2.40, 1.60, 0.18), mats["dark"], bevel=0.02)
    for fx in (-0.56, 0.56):
        cylinder("HVAC_RTU_FAN", (x + fx, y, 1.13), 0.37, 0.08, mats["dark"], rotation=(0, 0, 0))
        cylinder("HVAC_RTU_FAN_RING", (x + fx, y, 1.18), 0.41, 0.025, mats["metal"], rotation=(0, 0, 0))
    for i in range(7):
        cube("HVAC_RTU_LOUVER", (x - 1.131, y - 0.45 + i * 0.15, 0.58), (0.025, 0.09, 0.56), mats["dark"], bevel=0.004)


def setup_camera(bounds):
    min_x, min_y, max_x, max_y, max_z = bounds
    cx = (min_x + max_x) / 2
    cy = (min_y + max_y) / 2
    span = max(max_x - min_x, max_y - min_y, 3.0)
    camera_data = bpy.data.cameras.new("CAMERA")
    camera_data.lens = 46
    camera_data.sensor_width = 36
    camera = bpy.data.objects.new("CAMERA", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (cx + span * 1.22, cy - span * 1.45, max_z + span * 0.90)
    look_at(camera, (cx, cy, max_z * 0.38))
    bpy.context.scene.camera = camera
    return camera, (cx, cy, max_z * 0.40), span


def configure_render(payload, output_path):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    try:
        scene.render.engine = "CYCLES"
        scene.cycles.device = "CPU"
        scene.cycles.samples = int(payload.get("samples", 48))
        scene.cycles.use_denoising = True
    except Exception:
        scene.render.engine = "BLENDER_EEVEE_NEXT"

    scene.render.resolution_x = int(payload.get("width", 1536))
    scene.render.resolution_y = int(payload.get("height", 1024))
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.film_transparent = False
    scene.render.filepath = str(output_path)

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.035, 0.045, 0.065, 1.0)
    bg.inputs["Strength"].default_value = 0.28

    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        try:
            scene.view_settings.look = "Medium High Contrast"
        except Exception:
            pass
    scene.view_settings.exposure = 0.2


def main():
    request_path, output_path = argv_after_double_dash()
    payload = json.loads(Path(request_path).read_text(encoding="utf-8"))
    clear_scene()

    mats = {
        "floor": material("Oak Floor", (0.34, 0.19, 0.09), roughness=0.38),
        "wall": material("Warm White Wall", (0.88, 0.88, 0.84), roughness=0.72),
        "trim": material("White Trim", (0.96, 0.96, 0.96), roughness=0.42),
        "equipment": material("Equipment White", (0.82, 0.86, 0.88), roughness=0.34),
        "metal": material("Galvanized Metal", (0.38, 0.42, 0.45), roughness=0.30, metallic=0.78),
        "dark": material("Dark Mechanical", (0.035, 0.045, 0.055), roughness=0.28, metallic=0.35),
        "display": material("Display Glass", (0.02, 0.11, 0.14), roughness=0.12, metallic=0.05),
        "ground": material("Studio Ground", (0.08, 0.09, 0.11), roughness=0.58),
    }

    rooms = payload.get("rooms") or []
    gap = 0.75
    cursor_x = 0.0
    cursor_y = 0.0
    row_depth = 0.0
    room_geos = []
    max_x = max_y = max_z = 0.0

    for index, room in enumerate(rooms):
        if index and index % 3 == 0:
            cursor_x = 0.0
            cursor_y += row_depth + gap
            row_depth = 0.0
        geo = add_room(room, (cursor_x, cursor_y), mats)
        room_geos.append(geo)
        cursor_x += geo["width"] + gap
        row_depth = max(row_depth, geo["depth"])
        max_x = max(max_x, geo["origin"][0] + geo["width"])
        max_y = max(max_y, geo["origin"][1] + geo["depth"])
        max_z = max(max_z, geo["height"])

    brief = payload.get("brief") or {}
    text = " ".join(
        str(brief.get(key, ""))
        for key in ("projectTitle", "requestedChanges", "finishedProduct", "fieldNotes")
    ).lower()
    text += " " + str(payload.get("notes", "")).lower()

    if room_geos and any(term in text for term in ("mini split", "minisplit", "mini-split")):
        add_mini_split(room_geos[0], mats)
    if any(term in text for term in ("rtu", "rooftop unit", "package unit", "packaged unit")):
        add_rtu((max_x + 1.8, max(1.2, max_y * 0.45)), mats)
        max_x += 3.2
        max_z = max(max_z, 1.35)

    ground_w = max(max_x + 2.0, 6.0)
    ground_d = max(max_y + 2.0, 6.0)
    cube("GROUND", (ground_w / 2 - 1.0, ground_d / 2 - 1.0, -0.065), (ground_w, ground_d, 0.10), mats["ground"], bevel=0.01)

    camera, target, span = setup_camera((0.0, 0.0, max_x, max_y, max_z))
    add_area("KEY_LIGHT", (target[0] - span * 0.55, target[1] - span * 0.65, max_z + span * 1.15), 1450, max(2.5, span * 0.55), target)
    add_area("FILL_LIGHT", (target[0] + span * 0.75, target[1] - span * 0.15, max_z + span * 0.55), 760, max(2.0, span * 0.45), target)
    add_area("RIM_LIGHT", (target[0], target[1] + span * 0.85, max_z + span * 0.90), 1100, max(2.2, span * 0.50), target)

    sun_data = bpy.data.lights.new(name="SUN", type="SUN")
    sun_data.energy = 1.8
    sun_data.angle = math.radians(8)
    sun = bpy.data.objects.new("SUN", sun_data)
    bpy.context.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(28), math.radians(-18), math.radians(35))

    configure_render(payload, output_path)
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
