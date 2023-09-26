import pathlib
import datetime

import pytest

import wave_bwf_rf64


def test_reading_markers(markers_wavefile):
    has_r64m_chunk = markers_wavefile.read_r64m()
    assert has_r64m_chunk, "did not find r64m chunk?"

    markers = markers_wavefile.get_r64m_markers()
    assert markers[0].time_offset == datetime.timedelta(seconds=1, milliseconds=990)
    assert markers[0].label == "Test of special characters in UTF-8: Ođas ja áigeguovdil. Vuoiŋŋat. Sápmelaččain"

    assert markers[1].time_offset == datetime.timedelta(seconds=8, milliseconds=60)
    assert markers[1].label == "Test of special characters in Windows-1252: €æøåá"

    assert markers[2].time_offset == datetime.timedelta(seconds=11)
    assert markers[2].label == "From off to on"

    assert markers[3].time_offset == datetime.timedelta(seconds=12)
    assert markers[3].label == "From on to off"

    assert len(markers) == 4


@pytest.fixture
def markers_wavefile():
    this_dir = pathlib.Path(__file__).parent
    filepath = this_dir / 'markers.wav'
    wavefile = wave_bwf_rf64.open(str(filepath), "rb")
    try:
        yield wavefile
    finally:
        wavefile.close()
