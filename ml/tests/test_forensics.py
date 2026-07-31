"""Regression tests for the EXIF-based weak forgery signal.

The real bug this locks in: an earlier version flagged *missing* EXIF as
suspicious, which false-positived on every synthetic screenshot (and would
on every real one too, since screenshot-capture tools essentially never
embed camera EXIF regardless of authenticity). That check was removed --
only an explicit editor-software tag should ever fire.
"""

from PIL import Image

from features.forensics import check_exif_anomaly


def _save(path, exif_tags=None, fmt="PNG"):
    img = Image.new("RGB", (50, 50), "white")
    if exif_tags:
        exif = img.getexif()
        for tag_id, value in exif_tags.items():
            exif[tag_id] = value
        img.save(path, fmt, exif=exif)
    else:
        img.save(path, fmt)
    return str(path)


def test_missing_exif_is_not_flagged(tmp_path):
    # Regression: this used to be flagged and false-positived on every
    # screenshot. Screenshot tools essentially never embed EXIF.
    path = _save(tmp_path / "plain.png")
    result = check_exif_anomaly(path)
    assert result == {"possible_editing_signal": False, "reason": None}


def test_editor_software_tag_is_flagged(tmp_path):
    path = _save(tmp_path / "edited.jpg", {305: "Adobe Photoshop 24.0"}, fmt="jpeg")
    result = check_exif_anomaly(path)
    assert result["possible_editing_signal"] is True
    assert "Photoshop" in result["reason"]


def test_camera_exif_without_editor_tag_is_not_flagged(tmp_path):
    # EXIF present (a "Make" tag, as a real camera photo would have) but no
    # editor-software marker -- should not be flagged.
    path = _save(tmp_path / "camera.jpg", {271: "Samsung"}, fmt="jpeg")
    result = check_exif_anomaly(path)
    assert result == {"possible_editing_signal": False, "reason": None}


def test_gimp_is_also_recognized(tmp_path):
    path = _save(tmp_path / "gimp.jpg", {305: "GIMP 2.10"}, fmt="jpeg")
    result = check_exif_anomaly(path)
    assert result["possible_editing_signal"] is True


def test_nonexistent_file_does_not_raise(tmp_path):
    result = check_exif_anomaly(str(tmp_path / "does_not_exist.png"))
    assert result == {"possible_editing_signal": False, "reason": None}
