import pytest
from nornir.core import Nornir

from py_netauto.utils.nornir_helpers import initialize_nornir

# Setup


@pytest.fixture
def init_nornir():
    nr: Nornir = initialize_nornir()
    yield nr
    # Teardown
    nr.close_connections()


# Loading Data
