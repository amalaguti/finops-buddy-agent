"""Tests for demo mode masking functions."""

from finops_buddy.api.demo import (
    get_demo_system_prompt_addition,
    mask_account_id,
    mask_account_name,
    mask_response_data,
)


class TestMaskAccountName:
    """Tests for mask_account_name function."""

    def test_configured_mapping_applies(self):
        """WHEN demo mode is active AND account name matches configured mapping."""
        mapping = {"payer-profile": "Master_Account"}
        result = mask_account_name("payer-profile", mapping)
        assert result == "Master_Account"

    def test_unmapped_accounts_get_auto_generated_names(self):
        """WHEN demo mode is active AND account has no configured mapping."""
        mapping = {}
        result = mask_account_name("some-account", mapping)
        assert result == "Account_001"
        assert mapping["some-account"] == "Account_001"

    def test_auto_generation_increments(self):
        """Multiple unmapped accounts get sequential names."""
        mapping = {}
        result1 = mask_account_name("account-a", mapping)
        result2 = mask_account_name("account-b", mapping)
        result3 = mask_account_name("account-c", mapping)
        assert result1 == "Account_001"
        assert result2 == "Account_002"
        assert result3 == "Account_003"

    def test_same_account_returns_same_mask(self):
        """Calling with same account returns same masked name."""
        mapping = {}
        result1 = mask_account_name("test-account", mapping)
        result2 = mask_account_name("test-account", mapping)
        assert result1 == result2

    def test_empty_name_returns_empty(self):
        """Empty name is returned unchanged."""
        mapping = {}
        result = mask_account_name("", mapping)
        assert result == ""


class TestMaskAccountId:
    """Tests for mask_account_id function."""

    def test_configured_mapping_applies(self):
        """WHEN account ID matches configured mapping."""
        mapping = {"123456789012": "000000000001"}
        result = mask_account_id("123456789012", mapping)
        assert result == "000000000001"

    def test_unmapped_id_gets_auto_generated(self):
        """WHEN account ID has no configured mapping."""
        mapping = {}
        result = mask_account_id("123456789012", mapping)
        assert result == "000000000001"
        assert mapping["123456789012"] == "000000000001"

    def test_auto_generation_increments(self):
        """Multiple unmapped IDs get sequential values."""
        mapping = {}
        result1 = mask_account_id("111111111111", mapping)
        result2 = mask_account_id("222222222222", mapping)
        assert result1 == "000000000001"
        assert result2 == "000000000002"

    def test_empty_id_returns_empty(self):
        """Empty ID is returned unchanged."""
        mapping = {}
        result = mask_account_id("", mapping)
        assert result == ""


class TestMaskResponseData:
    """Tests for mask_response_data function."""

    def test_masks_profile_list(self):
        """WHEN API response contains profiles list."""
        name_mapping = {"real-profile": "Fake_Profile"}
        id_mapping = {}
        data = {"profiles": ["real-profile", "other-profile"]}
        result = mask_response_data(data, name_mapping, id_mapping)
        assert result["profiles"][0] == "Fake_Profile"
        assert result["profiles"][1] == "Account_001"

    def test_masks_master_profile_field(self):
        """WHEN API response contains master_profile field."""
        name_mapping = {"payer-profile": "Master_Account"}
        id_mapping = {}
        data = {"master_profile": "payer-profile"}
        result = mask_response_data(data, name_mapping, id_mapping)
        assert result["master_profile"] == "Master_Account"

    def test_masks_account_id_field(self):
        """WHEN API response contains account_id field."""
        name_mapping = {}
        id_mapping = {"123456789012": "000000000001"}
        data = {"account_id": "123456789012", "other": "value"}
        result = mask_response_data(data, name_mapping, id_mapping)
        assert result["account_id"] == "000000000001"
        assert result["other"] == "value"

    def test_masks_nested_data(self):
        """WHEN API response has nested structure."""
        name_mapping = {}
        id_mapping = {}
        data = {"context": {"account_id": "111111111111", "name": "test-account"}}
        result = mask_response_data(data, name_mapping, id_mapping)
        assert result["context"]["account_id"] == "000000000001"
        assert result["context"]["name"] == "Account_001"

    def test_masks_account_ids_in_strings(self):
        """WHEN string contains 12-digit account ID (like ARN)."""
        name_mapping = {}
        id_mapping = {}
        data = {"arn": "arn:aws:iam::123456789012:role/TestRole"}
        result = mask_response_data(data, name_mapping, id_mapping)
        assert "000000000001" in result["arn"]

    def test_masks_arn_assumed_role_session_name(self):
        """WHEN context contains assumed-role ARN, session name (e.g. email) is replaced."""
        from finops_buddy.api.demo import DEMO_MASK_ARN_SESSION_NAME

        name_mapping = {}
        id_mapping = {"644958719535": "000000000001"}
        data = {
            "arn": (
                "arn:aws:sts::644958719535:assumed-role/"
                "AWSReservedSSO_nv-role-finops-master_df241475fa4b2240/"
                "demo.user@example.com"
            ),
        }
        result = mask_response_data(data, name_mapping, id_mapping)
        assert result["arn"].endswith("/" + DEMO_MASK_ARN_SESSION_NAME)
        assert "demo.user@" not in result["arn"]
        assert "000000000001" in result["arn"]

    def test_non_demo_fields_unchanged(self):
        """Fields that don't contain account info remain unchanged."""
        name_mapping = {}
        id_mapping = {}
        data = {"service": "EC2", "cost": 123.45}
        result = mask_response_data(data, name_mapping, id_mapping)
        assert result["service"] == "EC2"
        assert result["cost"] == 123.45


class TestGetDemoSystemPromptAddition:
    """Tests for get_demo_system_prompt_addition function."""

    def test_includes_demo_mode_header(self):
        """System prompt addition includes DEMO MODE header."""
        result = get_demo_system_prompt_addition({})
        assert "DEMO MODE ACTIVE" in result

    def test_includes_configured_mappings(self):
        """System prompt includes configured account mappings."""
        mapping = {"payer-profile": "Master_Account", "prod": "Production"}
        result = get_demo_system_prompt_addition(mapping)
        assert '"payer-profile" → "Master_Account"' in result
        assert '"prod" → "Production"' in result

    def test_empty_mapping_shows_generic_instructions(self):
        """When no mapping configured, shows generic instructions."""
        result = get_demo_system_prompt_addition({})
        assert "generic names" in result.lower() or "Master_Account" in result
