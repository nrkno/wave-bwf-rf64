import pathlib

import wave_bwf_rf64


def test_writing_frames_without_setting_nframes_first(tmp_path: pathlib.Path):
    # Arrange
    wf = wave_bwf_rf64.open(str(tmp_path / 'test_writing_frames_without_setting_nframes_first.wav'), 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(48_000)

    # Act
    wf.writeframes(bytes.fromhex('01 00 02 00 03 00'))
    wf.close()

    # Assert
    assert wf.getnframes() == 3
