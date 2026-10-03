from backend.lite3.validation_profile import validate_boundary
import pytest


def baseline():
    return dict(source="NONE", autonomy_active=False, sable_active=False,
                receiver_count=1, high_level_count=1,
                params={"transmit": False, "zero_only": True, "require_deadman": True})


def test_inert_existing_runtime_is_accepted_without_ownership():
    state = baseline()
    assert validate_boundary(**state) is None
    assert state["source"] == "NONE"


@pytest.mark.parametrize("field,value", [("source", "AUTONOMY"),
    ("autonomy_active", True), ("sable_active", True),
    ("receiver_count", 2), ("high_level_count", 0)])
def test_unsafe_boundary_refuses_start(field, value):
    state = baseline()
    state[field] = value
    with pytest.raises(ValueError):
        validate_boundary(**state)


@pytest.mark.parametrize("params", [{}, {"transmit": True, "zero_only": True, "require_deadman": True},
    {"transmit": False, "zero_only": False, "require_deadman": True},
    {"transmit": False, "zero_only": True, "require_deadman": False}])
def test_missing_or_non_inert_parameters_refuse_start(params):
    state = baseline()
    state["params"] = params
    with pytest.raises(ValueError):
        validate_boundary(**state)
