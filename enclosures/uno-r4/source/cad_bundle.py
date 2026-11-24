#!/usr/bin/env python3
"""Export and inspect one CadQuery part, with explicit millimetre units.

Import ``export_bundle`` from this file. ``model`` must contain exactly one valid
positive-volume solid, already normalized to mm. ``profile`` is optional: pass an
explicit XY planar Face or Workplane containing closed wires for a flat cut file.
The helper never unfolds a model, selects a face, changes nominal dimensions,
repairs geometry, selects a fabrication process, or establishes vendor approval.
Some CAD-kernel tessellations (e.g. a sphere's poles) contain degenerate triangles;
these fail closed. Use mesh_formats=() for a solid-only bundle, or validate an
explicit alternate meshing procedure separately rather than suppressing errors.

The output directory must be new or empty. Returns a JSON-serializable report and
writes the same report to validation.json. Always check geometry_status; FAIL can
leave partial files for diagnosis. Contract errors (unsafe names, a nonempty
directory, non-JSON metadata) raise before writing. The caller owns drawing,
feature, material, tolerance, process, and vendor checks listed in ``unchecked``.

CLI: python cad_bundle.py --inspect-step path/to/part.step
Dependencies: CadQuery 2.7+, OCP (CadQuery dependency), ezdxf 1.4+.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import sys
from typing import Any

import cadquery as cq
from cadquery import exporters, importers
import ezdxf
from OCP.BRep import BRep_Tool
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopAbs import TopAbs_Orientation
from OCP.TopLoc import TopLoc_Location


SEAM_TOLERANCE_MM = 1e-7
ROUNDTRIP_ABSOLUTE_MM = 1e-6
ROUNDTRIP_RELATIVE = 1e-7


def _shape(value: Any) -> cq.Shape:
    if isinstance(value, cq.Workplane):
        items = value.vals()
        if not items or not all(isinstance(item, cq.Shape) for item in items):
            raise ValueError("Model Workplane must contain CAD shapes, not vectors or locations.")
        return items[0] if len(items) == 1 else cq.Compound.makeCompound(items)
    if not isinstance(value, cq.Shape):
        raise TypeError("Model must be a CadQuery Shape or Workplane.")
    return value


def _measure(shape: cq.Shape) -> dict:
    box = shape.BoundingBox()
    bounds = {
        "min": [box.xmin, box.ymin, box.zmin],
        "max": [box.xmax, box.ymax, box.zmax],
        "size": [box.xlen, box.ylen, box.zlen],
    }
    return {
        "solid_count": len(shape.Solids()),
        "valid": bool(shape.isValid()),
        "volume_mm3": shape.Volume(),
        "bounding_box_mm": bounds,
    }


def _validate_solid(shape: cq.Shape) -> dict:
    measured = _measure(shape)
    if measured["solid_count"] != 1:
        raise ValueError(f"Expected one solid; received {measured['solid_count']}.")
    if not measured["valid"]:
        raise ValueError("CAD kernel reports an invalid shape.")
    volume = measured["volume_mm3"]
    dimensions = measured["bounding_box_mm"]["size"]
    coordinates = measured["bounding_box_mm"]["min"] + measured["bounding_box_mm"]["max"]
    if not math.isfinite(volume) or volume <= 0:
        raise ValueError("Solid volume must be finite and positive.")
    if not all(math.isfinite(v) and v > 0 for v in dimensions):
        raise ValueError("All three solid dimensions must be finite and positive.")
    if not all(math.isfinite(v) for v in coordinates):
        raise ValueError("Solid coordinates must be finite.")
    # Reject a compound that hides loose faces, wires, or points beside its solid.
    solid = shape.Solids()[0]
    for getter in ("Faces", "Edges", "Vertices"):
        if len(getattr(shape, getter)()) != len(getattr(solid, getter)()):
            raise ValueError("Model includes loose geometry in addition to its solid.")
    return measured


def _near(a: float, b: float, absolute: float = ROUNDTRIP_ABSOLUTE_MM) -> bool:
    return abs(a - b) <= absolute + ROUNDTRIP_RELATIVE * max(abs(a), abs(b))


def _compare_solid(a: dict, b: dict) -> dict:
    volume_error = abs(a["volume_mm3"] - b["volume_mm3"])
    volume_ok = _near(a["volume_mm3"], b["volume_mm3"], 1e-6)
    aa = a["bounding_box_mm"]["min"] + a["bounding_box_mm"]["max"]
    bb = b["bounding_box_mm"]["min"] + b["bounding_box_mm"]["max"]
    bbox_ok = all(_near(x, y) for x, y in zip(aa, bb))
    return {
        "matches": volume_ok and bbox_ok,
        "volume_absolute_error_mm3": volume_error,
        "maximum_bound_error_mm": max(abs(x - y) for x, y in zip(aa, bb)),
        "absolute_bound_tolerance_mm": ROUNDTRIP_ABSOLUTE_MM,
        "absolute_volume_tolerance_mm3": 1e-6,
        "relative_tolerance": ROUNDTRIP_RELATIVE,
    }


def inspect_step(path: str | Path) -> dict:
    """Read a real STEP and return a single-solid check; never rewrite it."""
    path = Path(path)
    try:
        shape = _shape(importers.importStep(str(path)))
        measured = _validate_solid(shape)
        return {"geometry_status": "PASS", "units": "mm", "file": str(path), "model": measured}
    except Exception as exc:
        return {"geometry_status": "FAIL", "file": str(path), "error": str(exc)}


def _tessellate(shape: cq.Shape, linear: float, angular: float) -> tuple[list, list, dict]:
    """Mesh a copy with ABSOLUTE deflection; assemble coincident face seams."""
    meshed = shape.copy(mesh=False)
    job = BRepMesh_IncrementalMesh(meshed.wrapped, linear, False, angular, True)
    if not job.IsDone():
        raise ValueError("CAD kernel could not tessellate the solid.")
    vertices: list[tuple[float, float, float]] = []
    triangles: list[tuple[int, int, int]] = []
    indices: dict[tuple[int, int, int], int] = {}
    maximum_seam_distance = 0.0
    raw_vertex_count = 0
    for face in meshed.Faces():
        location = TopLoc_Location()
        poly = BRep_Tool.Triangulation_s(face.wrapped, location)
        if poly is None:
            raise ValueError("A CAD face has no triangulation.")
        transform = location.Transformation()
        reverse = face.wrapped.Orientation() == TopAbs_Orientation.TopAbs_REVERSED
        local = []
        for number in range(1, poly.NbNodes() + 1):
            p = poly.Node(number).Transformed(transform)
            point = (p.X(), p.Y(), p.Z())
            key = tuple(round(v / SEAM_TOLERANCE_MM) for v in point)
            index = indices.get(key)
            if index is None:
                index = len(vertices)
                vertices.append(point)
                indices[key] = index
            else:
                maximum_seam_distance = max(maximum_seam_distance, math.dist(point, vertices[index]))
            local.append(index)
            raw_vertex_count += 1
        for number in range(1, poly.NbTriangles() + 1):
            tri = poly.Triangle(number)
            order = (1, 3, 2) if reverse else (1, 2, 3)
            triangles.append(tuple(local[tri.Value(i) - 1] for i in order))
    return vertices, triangles, {
        "linear_deflection_mm": linear,
        "angular_deflection_rad": angular,
        "relative_deflection": False,
        "raw_face_vertex_count": raw_vertex_count,
        "assembled_vertex_count": len(vertices),
        "seam_coordinate_grid_mm": SEAM_TOLERANCE_MM,
        "maximum_shared_seam_distance_mm": maximum_seam_distance,
        "seam_note": "Only near-identical vertices from adjacent tessellated CAD faces share indices; no solid healing is performed.",
    }


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def _sub(a, b):
    return tuple(x-y for x, y in zip(a, b))


def _mesh_measure(vertices: list, triangles: list) -> dict:
    if not vertices or not triangles:
        raise ValueError("Empty mesh.")
    if not all(math.isfinite(c) for point in vertices for c in point):
        raise ValueError("Mesh has non-finite vertices.")
    undirected, directed = Counter(), Counter()
    degenerate, signed_volume, seen_faces, duplicates = 0, 0.0, set(), 0
    for tri in triangles:
        if len(tri) != 3 or any(i < 0 or i >= len(vertices) for i in tri):
            raise ValueError("Invalid triangle indices.")
        a, b, c = (vertices[i] for i in tri)
        normal = _cross(_sub(b, a), _sub(c, a))
        if len(set(tri)) != 3 or math.sqrt(sum(x*x for x in normal)) <= 1e-14:
            degenerate += 1
        key = tuple(sorted(tri))
        if key in seen_faces:
            duplicates += 1
        seen_faces.add(key)
        signed_volume += sum(x*y for x, y in zip(a, _cross(b, c))) / 6
        for x, y in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            undirected[tuple(sorted((x, y)))] += 1
            directed[(x, y)] += 1
    boundary = sum(count == 1 for count in undirected.values())
    nonmanifold = sum(count > 2 for count in undirected.values())
    orientation = sum(directed[(a, b)] != directed[(b, a)] for a, b in undirected)
    minimum = [min(point[i] for point in vertices) for i in range(3)]
    maximum = [max(point[i] for point in vertices) for i in range(3)]
    return {
        "vertices": len(vertices), "triangles": len(triangles),
        "boundary_edges": boundary, "nonmanifold_edges": nonmanifold,
        "orientation_conflicts": orientation, "degenerate_triangles": degenerate,
        "duplicate_triangles": duplicates, "signed_volume_mm3": signed_volume,
        "bounding_box_mm": {"min": minimum, "max": maximum, "size": _sub(maximum, minimum)},
        "basic_manifold_check_passed": boundary == nonmanifold == orientation == degenerate == duplicates == 0 and signed_volume > 0,
    }


def _write_stl(path: Path, vertices: list, triangles: list) -> None:
    with path.open("wb") as handle:
        handle.write(b"build-part; coordinates mm; prototype mesh".ljust(80, b" "))
        handle.write(struct.pack("<I", len(triangles)))
        for tri in triangles:
            a, b, c = (vertices[i] for i in tri)
            normal = _cross(_sub(b, a), _sub(c, a))
            norm = math.sqrt(sum(x*x for x in normal))
            unit = tuple(v/norm for v in normal)
            handle.write(struct.pack("<12fH", *unit, *a, *b, *c, 0))


def _read_stl(path: Path) -> tuple[list, list]:
    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError("Truncated binary STL.")
    count, = struct.unpack_from("<I", data, 80)
    if len(data) != 84 + count*50:
        raise ValueError("Binary STL length does not match its triangle count.")
    vertices, triangles, indices = [], [], {}
    for n in range(count):
        values = struct.unpack_from("<12fH", data, 84+n*50)
        tri = []
        for start in (3, 6, 9):
            point = tuple(values[start:start+3])
            if point not in indices:
                indices[point] = len(vertices)
                vertices.append(point)
            tri.append(indices[point])
        triangles.append(tuple(tri))
    return vertices, triangles


def _write_obj(path: Path, vertices: list, triangles: list) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("# build-part prototype mesh; coordinates are millimetres\n")
        for point in vertices:
            handle.write("v " + " ".join(format(c, ".17g") for c in point) + "\n")
        for tri in triangles:
            handle.write("f " + " ".join(str(i+1) for i in tri) + "\n")


def _read_obj(path: Path) -> tuple[list, list]:
    vertices, triangles = [], []
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if fields and fields[0] == "v":
            vertices.append(tuple(float(v) for v in fields[1:]))
        elif fields and fields[0] == "f":
            triangles.append(tuple(int(v)-1 for v in fields[1:]))
    return vertices, triangles


def _profile_shapes(value: Any) -> list[cq.Shape]:
    if isinstance(value, cq.Workplane):
        # Pending wires retain an outer contour through e.g. rect().pushPoints().circle().
        # Include stack values too, so an explicitly added contour is never dropped.
        candidates = list(value.ctx.pendingWires) + value.vals()
    elif isinstance(value, cq.Shape):
        candidates = [value]
    else:
        raise TypeError("Profile must be a CadQuery Face, Wire, or Workplane of closed wires.")
    if not candidates or not all(isinstance(item, (cq.Face, cq.Wire)) for item in candidates):
        raise ValueError("Profile must contain only faces or closed wires; no solids or loose edges.")
    unique = []
    for item in candidates:
        if not any(item.isSame(other) for other in unique):
            unique.append(item)
    return unique


def _entity_key(entity: Any) -> tuple:
    """Canonical signatures for exact/same-coordinate duplicate DXF entities."""
    def point(values):
        return tuple(round(float(v)/SEAM_TOLERANCE_MM) for v in values)

    kind = entity.dxftype()
    if kind == "LINE":
        return (kind, tuple(sorted((point(entity.dxf.start), point(entity.dxf.end)))))
    if kind == "CIRCLE":
        return (kind, point(entity.dxf.center), round(entity.dxf.radius/SEAM_TOLERANCE_MM))
    if kind == "ARC":
        return (kind, point(entity.dxf.center), round(entity.dxf.radius/SEAM_TOLERANCE_MM),
                round((entity.dxf.start_angle % 360)/1e-9), round((entity.dxf.end_angle % 360)/1e-9))
    if kind == "SPLINE":
        controls = tuple(point(p) for p in entity.control_points)
        fits = tuple(point(p) for p in entity.fit_points)
        return (kind, entity.dxf.degree, entity.dxf.flags, controls, fits,
                tuple(round(v/1e-10) for v in entity.knots), tuple(round(v/1e-10) for v in entity.weights))
    if kind == "ELLIPSE":
        return (kind, point(entity.dxf.center), point(entity.dxf.major_axis),
                round(entity.dxf.ratio/1e-10), round(entity.dxf.start_param/1e-10),
                round(entity.dxf.end_param/1e-10))
    if kind == "LWPOLYLINE":
        return (kind, bool(entity.closed), tuple(point(p) for p in entity.get_points()))
    if kind == "POLYLINE":
        return (kind, bool(entity.is_closed), tuple(point(v.dxf.location) for v in entity.vertices))
    raise ValueError(f"Cannot inspect duplicate {kind} entities.")


def _export_profile(profile: Any, path: Path, model: cq.Shape) -> dict:
    shapes = _profile_shapes(profile)
    wires = [wire for shape in shapes for wire in shape.Wires()]
    if not wires or not all(wire.IsClosed() and wire.isValid() for wire in wires):
        raise ValueError("Every cut contour must be valid and closed.")
    compound = cq.Compound.makeCompound(shapes)
    bounds = compound.BoundingBox()
    if bounds.zlen > SEAM_TOLERANCE_MM:
        raise ValueError("Cut profile must be parallel to XY; no projection or unfolding is performed.")
    for wire in wires:
        if not cq.Face.makeFromWires(wire).isValid():
            raise ValueError("A cut contour cannot form a valid planar face.")
    flat = compound.translate((0, 0, -bounds.zmin))
    exporters.exportDXF(flat, str(path), doc_units=4)
    document = ezdxf.readfile(path)
    if document.units != 4:
        raise ValueError("Reopened DXF does not declare millimetres.")
    audit = document.audit()
    if audit.has_errors or audit.has_fixes:
        raise ValueError("Reopened DXF requires repairs; file was not silently healed.")
    entities = list(document.modelspace())
    allowed = {"LINE", "ARC", "CIRCLE", "ELLIPSE", "SPLINE", "LWPOLYLINE", "POLYLINE"}
    if not entities or any(entity.dxftype() not in allowed for entity in entities):
        raise ValueError("DXF contains unsupported geometry or annotations.")
    layers = sorted({entity.dxf.layer for entity in entities})
    if len(layers) != 1:
        raise ValueError("Basic cut DXF must have one geometry layer.")
    signatures = [_entity_key(entity) for entity in entities]
    if len(signatures) != len(set(signatures)):
        raise ValueError("DXF contains duplicate cutting entities.")
    # Kernel round-trip verifies the emitted contours as wires, beyond the original input.
    reopened = importers.importDXF(str(path), tol=SEAM_TOLERANCE_MM)
    imported_wires = list(reopened.ctx.pendingWires) or reopened.wires().vals()
    if len(imported_wires) != len(wires) or not all(w.IsClosed() for w in imported_wires):
        raise ValueError("Reopened DXF lost, joined, or opened a cut contour.")
    original_lengths = sorted(w.Length() for w in wires)
    imported_lengths = sorted(w.Length() for w in imported_wires)
    if not all(_near(a, b) for a, b in zip(original_lengths, imported_lengths)):
        raise ValueError("Reopened DXF contour lengths differ from source.")
    # Canonical edge endpoints/centres catch exact duplicate cutting entities.
    # Because repeated wire imports may be joined, also compare edge totals.
    original_edges = sum(len(w.Edges()) for w in wires)
    imported_edges = sum(len(w.Edges()) for w in imported_wires)
    if original_edges != imported_edges or len(entities) != original_edges:
        raise ValueError("DXF edge count changed or contains duplicate/stray entities.")
    new_bounds = cq.Compound.makeCompound(imported_wires).BoundingBox()
    if not all(_near(a, b) for a, b in zip(
        (bounds.xmin, bounds.xmax, bounds.ymin, bounds.ymax),
        (new_bounds.xmin, new_bounds.xmax, new_bounds.ymin, new_bounds.ymax),
    )):
        raise ValueError("DXF planar bounds differ from source.")
    relation = {"status": "UNVERIFIED", "reason": "The profile-to-finished-solid relation requires explicit review."}
    if len(shapes) == 1 and isinstance(shapes[0], cq.Face):
        face = shapes[0].translate((0, 0, -bounds.zmin))
        model_box = model.BoundingBox()
        prism = cq.Solid.extrudeLinear(face.outerWire(), face.innerWires(), (0, 0, model_box.zlen))
        prism = prism.translate((0, 0, model_box.zmin))
        excess = abs(prism.cut(model).Volume()) + abs(model.cut(prism).Volume())
        allowance = max(1e-6, model.Volume()*1e-7)
        relation = {
            "status": "PASS" if excess <= allowance else "UNVERIFIED",
            "symmetric_difference_volume_mm3": excess,
            "volume_tolerance_mm3": allowance,
            "reason": "Compared the explicit profile extruded through model Z thickness against the solid; secondary operations may require a separate blank model.",
        }
    return {
        "units": "mm", "input_plane_z_mm": bounds.zmin,
        "export_plane_z_mm": 0, "closed_contours": len(wires),
        "entities": len(entities), "entity_types": dict(Counter(e.dxftype() for e in entities)),
        "layers": layers, "roundtrip_closed_contours": len(imported_wires),
        "duplicate_entities": 0,
        "bounding_box_xy_mm": [bounds.xmin, bounds.ymin, bounds.xmax, bounds.ymax],
        "profile_to_solid": relation,
        "curve_note": "Analytic curves retained where exporter supports them; spline acceptability still requires vendor review.",
    }


def export_bundle(
    model: Any,
    output_dir: str | Path,
    part_id: str,
    revision: str = "A",
    profile: Any = None,
    mesh_formats: tuple[str, ...] = ("stl", "obj"),
    metadata: dict | None = None,
    linear_tolerance_mm: float = 0.02,
    angular_tolerance_rad: float = 0.1,
) -> dict:
    """Build a revision's geometry files; see module docstring for the contract."""
    for label, value in (("part_id", part_id), ("revision", revision)):
        if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}", value):
            raise ValueError(f"{label} must be a safe filename component (letters, numbers, dot, underscore, dash).")
    if not all(math.isfinite(v) and v > 0 for v in (linear_tolerance_mm, angular_tolerance_rad)):
        raise ValueError("Meshing tolerances must be finite and positive.")
    formats = tuple(dict.fromkeys(str(ext).lower().lstrip(".") for ext in mesh_formats))
    if any(ext not in ("stl", "obj") for ext in formats):
        raise ValueError("Supported prototype mesh formats are stl and obj.")
    metadata = {} if metadata is None else metadata
    json.dumps(metadata, allow_nan=False)
    output = Path(output_dir).resolve()
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise FileExistsError("Output directory must be new or empty; use a new revision/output path.")
    output.mkdir(parents=True, exist_ok=True)
    name = f"{part_id}_rev-{revision}_mm"
    report = {
        "schema_version": 1, "geometry_status": "FAIL", "scope": "file_geometry_only",
        "part_id": part_id, "revision": revision, "units": "mm",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "software": {"cadquery": cq.__version__, "ezdxf": ezdxf.__version__},
        "metadata": metadata, "checks": [], "files": [], "errors": [],
        "unchecked": [
            "Description, feature dimensions, and fit intent against CAD and drawing.",
            "Drawing view, dimension, tolerance, material, and revision correctness.",
            "Current vendor material, thickness, process, bend, and minimum-feature rules.",
            "Structural strength, fatigue, thermal behavior, and service-load suitability.",
            "Vendor upload preview, selected services, quoted dimensions, and manufacturing acceptance.",
        ],
    }

    def record(name: str, details: dict, status: str = "PASS"):
        report["checks"].append({"name": name, "status": status, "details": details})

    def file_record(path: Path, role: str):
        data = path.read_bytes()
        report["files"].append({"path": path.relative_to(output).as_posix(), "role": role,
                                "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})

    stage = "input_solid"
    try:
        shape = _shape(model)
        report["model"] = _validate_solid(shape)
        record(stage, report["model"])
        (output/"cad").mkdir()
        step_path = output/"cad"/(name+".step")
        stage = "step_roundtrip"
        exporters.export(shape, str(step_path), exportType="STEP")
        reopened = _validate_solid(_shape(importers.importStep(str(step_path))))
        comparison = _compare_solid(report["model"], reopened)
        if not comparison["matches"]:
            raise ValueError("STEP round-trip dimensions or volume differ from the model.")
        record(stage, {"reopened_model": reopened, "comparison": comparison})
        file_record(step_path, "solid_cad")

        if formats:
            stage = "mesh_geometry"
            vertices, triangles, settings = _tessellate(shape, linear_tolerance_mm, angular_tolerance_rad)
            mesh = _mesh_measure(vertices, triangles)
            if not mesh["basic_manifold_check_passed"]:
                raise ValueError(f"Tessellated mesh failed basic manifold checks: {mesh}")
            mesh["volume_relative_error_vs_solid"] = abs(mesh["signed_volume_mm3"]-shape.Volume())/shape.Volume()
            record(stage, {"settings": settings, "measurements": mesh})
            report["unchecked"].append("Mesh self-intersections and local geometric deviation from CAD are not exhaustively measured; deflection settings and basic topology are checked.")
            report["unchecked"].append("STL and OBJ are unitless formats; import their coordinates as millimetres and verify scale.")
            (output/"prototypes").mkdir()
            for extension in formats:
                stage = extension+"_roundtrip"
                path = output/"prototypes"/(name+"."+extension)
                (_write_stl if extension == "stl" else _write_obj)(path, vertices, triangles)
                vv, tt = (_read_stl if extension == "stl" else _read_obj)(path)
                measured = _mesh_measure(vv, tt)
                if not measured["basic_manifold_check_passed"] or len(tt) != len(triangles):
                    raise ValueError(f"Reopened {extension.upper()} failed mesh topology checks.")
                bounds_a = mesh["bounding_box_mm"]["min"]+mesh["bounding_box_mm"]["max"]
                bounds_b = measured["bounding_box_mm"]["min"]+measured["bounding_box_mm"]["max"]
                if not all(_near(a, b) for a, b in zip(bounds_a, bounds_b)):
                    raise ValueError(f"Reopened {extension.upper()} changed dimensions.")
                record(stage, measured)
                file_record(path, "prototype_mesh")

        if profile is not None:
            stage = "dxf_roundtrip"
            (output/"fabrication").mkdir()
            path = output/"fabrication"/(name+"_cut.dxf")
            result = _export_profile(profile, path, shape)
            record(stage, result)
            if result["profile_to_solid"]["status"] != "PASS":
                report["unchecked"].append("DXF cut profile versus finished solid requires an explicit geometric/secondary-operation mapping; automatic extrusion equivalence was not established.")
            file_record(path, "flat_cut_geometry")

        stage = "svg_preview"
        (output/"previews").mkdir()
        path = output/"previews"/(name+"_isometric.svg")
        path.write_text(exporters.getSVG(shape, {"width": 900, "height": 650, "marginLeft": 30, "marginTop": 30, "showAxes": False, "projectionDir": (1, -1, 1), "showHidden": False}), encoding="utf-8")
        file_record(path, "undimensioned_preview")
        record(stage, {"note": "CAD-projected isometric preview; visual inspection remains required."})
        report["geometry_status"] = "PASS"
    except Exception as exc:
        report["errors"].append(f"{stage}: {type(exc).__name__}: {exc}")
        record(stage, {"error": str(exc)}, "FAIL")
    (output/"validation.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inspect-step", type=Path, required=True, help="Read-only STEP single-solid inspection")
    args = parser.parse_args()
    result = inspect_step(args.inspect_step)
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result["geometry_status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
