import os
import shutil
import subprocess
import json # Re-added for reading language files
import pytest
from create_test_data import setup_initial_mods, setup_updated_mods, create_dummy_jar

MODS_DIR = "tests/mock_mods"
RP_DIR = "tests/mock_resource_pack"

@pytest.fixture(scope="module")
def setup_test_environment():
    """Cleans and sets up test directories once per module."""
    print("\n--- Setting up test environment ---")
    if os.path.exists(RP_DIR):
        shutil.rmtree(RP_DIR)
    os.makedirs(RP_DIR)
    if os.path.exists(MODS_DIR):
        shutil.rmtree(MODS_DIR)
    os.makedirs(MODS_DIR)
    yield
    print("\n--- Tearing down test environment ---")
    # Optional: clean up after tests if needed, but usually fixtures handle setup/teardown

def run_uplang_command(command_args):
    """Runs an uplang command and asserts its success."""
    print(f"\n--- Running command: uplang {command_args} ---")
    full_command = ["python", "-m", "uplang.cli"] + command_args.split()
    env = os.environ.copy()
    env['PYTHONPATH'] = '/mnt/d/QianFuv/UpLang/src'
    result = subprocess.run(
        full_command,
        capture_output=True,
        text=True,
        encoding='utf-8',
        check=False,
        env=env
    )
    print(result.stdout)
    if result.stderr:
        print("--- Stderr ---")
        print(result.stderr)
    assert result.returncode == 0, f"Command 'uplang {command_args}' failed with exit code {result.returncode}. Stderr: {result.stderr}"
    return result.stdout

def test_init_command(setup_test_environment):
    """Tests the 'init' command functionality."""
    print("\n--- Running Init Command Test ---")
    setup_initial_mods()
    run_uplang_command(f"init {MODS_DIR} {RP_DIR}")

    print("\n--- Verifying 'init' results ---")
    assert os.path.exists(f"{RP_DIR}/assets/forge_mod/lang/en_us.json")
    assert os.path.exists(f"{RP_DIR}/assets/forge_mod/lang/zh_cn.json")
    assert os.path.exists(f"{RP_DIR}/assets/fabric_mod/lang/en_us.json")
    assert os.path.exists(f"{RP_DIR}/assets/no_meta_mod/lang/en_us.json")
    assert os.path.exists(f"{RP_DIR}/assets/no_meta_mod/lang/zh_cn.json")
    assert os.path.exists(f"{RP_DIR}/.uplang_state.json")
    print("Init verification successful.")

def test_check_command(setup_test_environment):
    """Tests the 'check' command functionality."""
    print("\n--- Running Check Command Test ---")
    # Ensure initial state is set up before checking
    setup_initial_mods()
    run_uplang_command(f"init {MODS_DIR} {RP_DIR}")

    setup_updated_mods()
    run_uplang_command(f"check {MODS_DIR} {RP_DIR}")

    print("\n--- Verifying 'check' results ---")
    assert os.path.exists(f"{RP_DIR}/assets/new_mod/lang/zh_cn.json")

    zh_cn_path = f"{RP_DIR}/assets/forge_mod/lang/zh_cn.json"
    with open(zh_cn_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert "key.three" in data, "Updated key 'key.three' not found in zh_cn.json"

    zh_cn_path_no_meta = f"{RP_DIR}/assets/no_meta_mod/lang/zh_cn.json"
    with open(zh_cn_path_no_meta, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert "key.no_meta_new" in data, "Updated key 'key.no_meta_new' not found in zh_cn.json for no-meta mod"
    print("Check verification successful.")

def test_language_file_synchronization(setup_test_environment):
    """Tests the language file synchronization feature (add/remove keys)."""
    print("\n--- Running Language File Synchronization Test ---")

    mod_id = "sync_mod"
    rp_mod_dir = os.path.join(RP_DIR, "assets", mod_id, "lang")
    en_us_path = os.path.join(rp_mod_dir, "en_us.json")
    zh_cn_path = os.path.join(rp_mod_dir, "zh_cn.json")

    # 1. Create a dummy mod JAR for sync_mod in MODS_DIR
    # This will ensure uplang check can discover it.
    # We need to create a temporary mod file for this.
    # For simplicity, let's create a dummy file that create_test_data.py can pick up.
    # create_test_data.py expects a list of mod_ids to create.
    # Let's temporarily modify create_test_data.py or call its internal function.
    # A simpler approach for this test is to directly create a dummy JAR.
    # However, create_test_data.py is designed for this.
    # Let's assume create_test_data.setup_initial_mods() creates a mod with mod_id "forge_mod"
    # and we will use that for our synchronization test.

    # Setup initial mods, including one we'll use for sync test
    # This will create forge_mod_v1.jar in MODS_DIR and initialize its lang files
    setup_initial_mods()
    run_uplang_command(f"init {MODS_DIR} {RP_DIR}")

    # Now, forge_mod's language files exist in the resource pack.
    # We will use forge_mod for our synchronization test.
    sync_mod_id = "forge_mod"
    rp_sync_mod_dir = os.path.join(RP_DIR, "assets", sync_mod_id, "lang")
    en_us_path = os.path.join(rp_sync_mod_dir, "en_us.json")
    zh_cn_path = os.path.join(rp_sync_mod_dir, "zh_cn.json")

    # Initial en_us.json (from setup_initial_mods)
    # Initial zh_cn.json (from setup_initial_mods, copy of en_us)

    # Modify zh_cn.json to have a key to be removed and an existing key with translation
    initial_zh_cn_data = {
        "key.common.world": "世界", # Existing key with translation
        "key.to.be.removed": "将被删除的键", # Key to be removed
        "item.forge_mod.item_one": "物品一" # Key from initial en_us.json
    }
    with open(zh_cn_path, 'w', encoding='utf-8') as f:
        json.dump(initial_zh_cn_data, f, indent=4)

    # Simulate an update to en_us.json for forge_mod
    # This will trigger the synchronization logic in the check command
    updated_en_us_data = {
        "key.common.hello": "Hello", # New key to be added
        "key.common.world": "World", # Existing key
        "key.new.feature": "New Feature", # Another new key
        "item.forge_mod.item_one": "Item One" # Existing key
    }
    # Overwrite en_us.json with updated content
    with open(en_us_path, 'w', encoding='utf-8') as f:
        json.dump(updated_en_us_data, f, indent=4)

    # Run the check command
    # This will process forge_mod as an updated mod and trigger synchronization
    run_uplang_command(f"check {MODS_DIR} {RP_DIR}")

    print("\n--- Verifying Language File Synchronization results ---")
    with open(zh_cn_path, 'r', encoding='utf-8') as f:
        synchronized_zh_cn_data = json.load(f)

    # Assertions
    assert "key.common.hello" in synchronized_zh_cn_data # New key should be added
    assert synchronized_zh_cn_data["key.common.hello"] == "Hello"

    assert "key.new.feature" in synchronized_zh_cn_data # Another new key should be added
    assert synchronized_zh_cn_data["key.new.feature"] == "New Feature"

    assert "key.to.be.removed" not in synchronized_zh_cn_data # Key should be removed

    # Ensure existing key's value is preserved if it exists in both
    assert synchronized_zh_cn_data["key.common.world"] == "世界"
    assert synchronized_zh_cn_data["item.forge_mod.item_one"] == "物品一"

    print("Language File Synchronization verification successful.")

def test_init_with_existing_zh_cn_and_synchronization(setup_test_environment):
    """
    Tests the 'init' command when a mod JAR contains an existing zh_cn.json,
    ensuring it's copied and then synchronized with en_us.json.
    """
    print("\n--- Running Init with Existing zh_cn.json Test ---")

    mod_id = "init_sync_mod"
    mod_jar_name = f"{mod_id}_v1.jar"
    rp_mod_dir = os.path.join(RP_DIR, "assets", mod_id, "lang")
    en_us_path = os.path.join(rp_mod_dir, "en_us.json")
    zh_cn_path = os.path.join(rp_mod_dir, "zh_cn.json")

    # Define en_us.json content for the dummy mod
    en_us_content = {
        "key.init.hello": "Hello Init",
        "key.init.world": "World Init",
        "key.init.new": "New Key Init"
    }

    # Define zh_cn.json content for the dummy mod (with a key to be removed)
    zh_cn_content_in_jar = {
        "key.init.world": "世界初始化",
        "key.init.old": "旧键初始化" # This key should be removed by synchronization
    }

    # Create the dummy mod JAR with both en_us.json and zh_cn.json
    create_dummy_jar(
        mod_jar_name,
        mod_id,
        "1.0.0",
        en_us_content,
        zh_cn_content=zh_cn_content_in_jar,
        mod_type="forge"
    )

    # Run the init command
    run_uplang_command(f"init {MODS_DIR} {RP_DIR}")

    print("\n--- Verifying Init with Existing zh_cn.json results ---")

    # Assert en_us.json exists and has correct content
    assert os.path.exists(en_us_path)
    with open(en_us_path, 'r', encoding='utf-8') as f:
        loaded_en_us = json.load(f)
    assert loaded_en_us == en_us_content

    # Assert zh_cn.json exists and is synchronized
    assert os.path.exists(zh_cn_path)
    with open(zh_cn_path, 'r', encoding='utf-8') as f:
        synchronized_zh_cn_data = json.load(f)

    # Assertions for synchronization
    assert "key.init.hello" in synchronized_zh_cn_data # Should be added
    assert synchronized_zh_cn_data["key.init.hello"] == "Hello Init"

    assert "key.init.new" in synchronized_zh_cn_data # Should be added
    assert synchronized_zh_cn_data["key.init.new"] == "New Key Init"

    assert "key.init.old" not in synchronized_zh_cn_data # Should be removed

    assert synchronized_zh_cn_data["key.init.world"] == "世界初始化" # Should retain original translation

    print("Init with Existing zh_cn.json verification successful.")