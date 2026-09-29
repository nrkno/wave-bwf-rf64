import pathlib

import wave_bwf_rf64


def test_reading_on_big_endian(tmp_path: pathlib.Path, monkeypatch):
    # Arrange
    filename = str(tmp_path / 'test_reading_on_big_endian.wav')

    with monkeypatch.context() as m:
        m.setattr(wave_bwf_rf64.wave.sys, 'byteorder', 'little')

        wf = wave_bwf_rf64.open(filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(48_000)
        wf.setnframes(3)

        wf.writeframes(bytes.fromhex('00 01 00 02 00 03'))
        wf.close()

    # Act
    with monkeypatch.context() as m:
        m.setattr(wave_bwf_rf64.wave.sys, 'byteorder', 'big')

        wf = wave_bwf_rf64.open(filename, 'rb')

        # The bytes should be swapped from little to big endian when reading
        audio_frames = wf.readframes(3)

        wf.close()

    # Assert
    assert audio_frames == bytes.fromhex('01 00 02 00 03 00')
