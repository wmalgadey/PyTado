import pytest

from PyTado.__main__ import main

def test_entry_point_no_args():
    with pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 2
