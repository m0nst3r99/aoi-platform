from dataclasses import replace

import pytest

from aoi_platform.geometry import AxisDirection, Frame, FrameKind, Unit


@pytest.fixture
def mm_frame() -> Frame:
    return Frame(
        frame_id="fixture/rev-a/source-mm", kind=FrameKind.SOURCE, unit=Unit.MM,
        origin="declared source datum", x_direction=AxisDirection.RIGHT,
        y_direction=AxisDirection.UP, board_revision_id="fixture/rev-a",
    )


@pytest.fixture
def inch_frame(mm_frame: Frame) -> Frame:
    return replace(mm_frame, frame_id="fixture/rev-a/source-inch", unit=Unit.INCH)
