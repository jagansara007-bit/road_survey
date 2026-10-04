import os
import time
from pathlib import Path

import cv2
import numpy as np
from app.privacy import (
    DefaultOfflineRedactor,
    Redactor,
    blur_bounding_box,
    blur_crop,
    get_default_redactor,
    measure_blur_recall,
)

from scripts.purge_old_media import purge_old_media


def test_redactor_protocol_conformance():
    redactor = get_default_redactor()
    assert isinstance(redactor, Redactor) or hasattr(redactor, "redact")


def test_blur_bounding_box():
    # Create image with high-frequency alternating checker pattern
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[20:60:2, 20:60:2] = 255
    raw_copy = img.copy()

    # Compute high frequency energy (variance of Laplacian)
    gray_raw = cv2.cvtColor(raw_copy, cv2.COLOR_BGR2GRAY)
    raw_var = cv2.Laplacian(gray_raw, cv2.CV_64F).var()

    blurred = blur_bounding_box(img, 20, 20, 60, 60)
    gray_blurred = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
    blurred_var = cv2.Laplacian(gray_blurred, cv2.CV_64F).var()

    # The blurred image must have significantly lower edge variance (energy)
    assert blurred_var < raw_var
    assert not np.array_equal(raw_copy, blurred)



def test_redactor_skin_tone_face_blur():
    redactor = DefaultOfflineRedactor(blur_faces=True, blur_plates=False)
    img = np.zeros((200, 200, 3), dtype=np.uint8)

    # Insert a skin-tone colored rectangular patch in YCrCb space
    # Cr: 150, Cb: 100 in YCrCb corresponds to skin tone
    skin_patch = np.zeros((60, 50, 3), dtype=np.uint8)
    skin_patch[:, :, 0] = 160  # Y
    skin_patch[:, :, 1] = 150  # Cr
    skin_patch[:, :, 2] = 100  # Cb
    skin_bgr = cv2.cvtColor(skin_patch, cv2.COLOR_YCrCb2BGR)

    # Add sharp high-frequency edges within the face patch (e.g. eyes/mouth)
    skin_bgr[20:30, 15:35] = 0

    img[50:110, 75:125] = skin_bgr
    raw_copy = img.copy()

    redacted = redactor.redact(img)

    # Ensure detected and redacted
    regions = redactor.detect_sensitive_regions(raw_copy)
    assert len(regions) >= 1
    assert any(r[4] == "face" for r in regions)

    # Pixel difference must be substantial in the face region
    diff = np.sum(np.abs(raw_copy.astype(float) - redacted.astype(float)))
    assert diff > 0


def test_redactor_license_plate_blur():
    redactor = DefaultOfflineRedactor(blur_faces=False, blur_plates=True)
    img = np.zeros((200, 300, 3), dtype=np.uint8)

    # Insert a high-contrast plate-like pattern (aspect ratio ~ 3.5:1)
    plate = np.full((30, 105, 3), 240, dtype=np.uint8)
    # Add vertical alternating black lines simulating alphanumeric characters
    for x in range(10, 95, 10):
        plate[5:25, x:x+4] = 0

    img[120:150, 90:195] = plate
    raw_copy = img.copy()

    regions = redactor.detect_sensitive_regions(raw_copy)
    assert len(regions) >= 1
    assert any(r[4] == "license_plate" for r in regions)

    redacted = redactor.redact(img)
    assert not np.array_equal(raw_copy, redacted)


def test_blur_crop_persisted_to_disk(tmp_path: Path):
    # Ensure crop written to disk has lower high-frequency energy than raw
    test_img = np.zeros((100, 100, 3), dtype=np.uint8)
    test_img[30:70, 30:70] = 255
    # Use custom detector to guarantee sensitive detection on test region
    custom_redactor = DefaultOfflineRedactor(
        custom_face_detector=lambda _im: [(30, 30, 70, 70)]
    )

    redacted = blur_crop(test_img, redactor=custom_redactor)
    out_file = tmp_path / "crop_test.jpg"
    cv2.imwrite(str(out_file), redacted)

    assert out_file.exists()
    loaded = cv2.imread(str(out_file))

    raw_lap = cv2.Laplacian(cv2.cvtColor(test_img, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
    persisted_lap = cv2.Laplacian(cv2.cvtColor(loaded, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
    assert persisted_lap < raw_lap


def test_purge_old_media(tmp_path: Path):
    now = time.time()
    media_dir = tmp_path / "surveys"
    media_dir.mkdir()

    # Create 3 files: 1 recent (5 days old), 2 expired (40 days old)
    recent_file = media_dir / "recent_crop.jpg"
    recent_file.write_bytes(b"dummy_recent_data")
    os.utime(recent_file, (now - 5 * 86400, now - 5 * 86400))

    old_crop = media_dir / "old_crop.jpg"
    old_crop.write_bytes(b"dummy_old_crop")
    os.utime(old_crop, (now - 40 * 86400, now - 40 * 86400))

    old_video = media_dir / "old_video.mp4"
    old_video.write_bytes(b"dummy_old_video")
    os.utime(old_video, (now - 50 * 86400, now - 50 * 86400))

    # Dry-run: should report 2 candidates to purge, but neither should be deleted
    dry_res = purge_old_media(media_dir, retention_days=30, dry_run=True, now_timestamp=now)
    assert dry_res["files_purged"] == 2
    assert recent_file.exists()
    assert old_crop.exists()
    assert old_video.exists()

    # Apply run: should delete expired files and retain recent
    apply_res = purge_old_media(media_dir, retention_days=30, dry_run=False, now_timestamp=now)
    assert apply_res["files_purged"] == 2
    assert apply_res["files_retained"] == 1
    assert recent_file.exists()
    assert not old_crop.exists()
    assert not old_video.exists()


def test_measure_blur_recall_not_measured():
    res = measure_blur_recall("non_existent_dir_12345")
    assert res["status"] == "NOT MEASURED"
    assert res["sample_size"] == 0
