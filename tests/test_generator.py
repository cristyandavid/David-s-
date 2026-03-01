import pytest
from src.generator import generate, SUPPORTED_TYPES


def test_generate_returns_nonempty_string():
    result = generate("erc20", {"name": "TestToken"})
    assert isinstance(result, str)
    assert len(result) > 0


def test_generate_includes_contract_name():
    result = generate("erc721", {"name": "MyNFT"})
    assert "MyNFT" in result


def test_generate_includes_solidity_header():
    result = generate("multisig", {"name": "Vault"})
    assert "pragma solidity" in result


def test_generate_all_supported_types():
    for contract_type in SUPPORTED_TYPES:
        result = generate(contract_type, {"name": "Smoke"})
        assert result, f"Expected non-empty output for type '{contract_type}'"


def test_generate_raises_on_unknown_type():
    with pytest.raises(ValueError, match="Unsupported contract type"):
        generate("unknown_type", {})
