import os
import zipfile
import json

MODS_DIR = "tests/mock_mods"

def create_dummy_jar(
    file_name, mod_id, version, en_us_content, zh_cn_content=None, mod_type="forge", create_metadata=True
):
    """Creates a dummy .jar file with specified metadata and language files."""
    path = os.path.join(MODS_DIR, file_name)
    with zipfile.ZipFile(path, "w") as zf:
        if create_metadata:
            if mod_type == "forge":
                metadata_path = "META-INF/mods.toml"
                metadata_content = f"""\
modLoader="javafml"
loaderVersion="[47,)"
license="All Rights Reserved"
[[mods]]
modId="{mod_id}"
version="{version}"
"""
                zf.writestr(metadata_path, metadata_content)
            elif mod_type == "fabric":
                metadata_path = "fabric.mod.json"
                metadata_content = json.dumps(
                    {"schemaVersion": 1, "id": mod_id, "version": version}
                )
                zf.writestr(metadata_path, metadata_content)

        # Write en_us.json
        en_us_path = f"assets/{mod_id}/lang/en_us.json"
        zf.writestr(en_us_path, json.dumps(en_us_content, indent=4))

        # Write zh_cn.json if provided
        if zh_cn_content is not None:
            zh_cn_path = f"assets/{mod_id}/lang/zh_cn.json"
            zf.writestr(zh_cn_path, json.dumps(zh_cn_content, indent=4))
    print(f"Created dummy mod: {file_name}")


def setup_initial_mods():
    """Creates the initial set of mods for testing the 'init' command.""" 
    if not os.path.exists(MODS_DIR):
        os.makedirs(MODS_DIR)
    for f in os.listdir(MODS_DIR):
        os.remove(os.path.join(MODS_DIR, f))

    create_dummy_jar(
        "forge_mod_v1.jar",
        "forge_mod",
        "1.0.0",
        {"key.one": "First Key", "key.two": "Second Key"},
        "forge",
    )
    create_dummy_jar(
        "fabric_mod_v1.jar",
        "fabric_mod",
        "1.0.0",
        {"key.a": "Key A", "key.b": "Key B"},
        "fabric",
    )
    create_dummy_jar(
        "no_meta_mod_v1.jar",
        "no_meta_mod",
        "1.0.0",
        {"key.no_meta": "No Meta Key"},
        create_metadata=False,
    )


def setup_updated_mods():
    """Creates the updated set of mods for testing the 'check' command."""
    os.remove(os.path.join(MODS_DIR, "forge_mod_v1.jar"))
    os.remove(os.path.join(MODS_DIR, "no_meta_mod_v1.jar"))

    create_dummy_jar(
        "forge_mod_v2.jar",
        "forge_mod",
        "2.0.0",
        {"key.one": "First Key", "key.two": "Second Key", "key.three": "Third Key"},
        "forge",
    )
    create_dummy_jar(
        "new_mod_v1.jar", "new_mod", "1.0.0", {"key.new": "New Key"}, "forge"
    )
    create_dummy_jar(
        "no_meta_mod_v2.jar",
        "no_meta_mod",
        "2.0.0",
        {"key.no_meta": "No Meta Key", "key.no_meta_new": "New No Meta Key"},
        create_metadata=False,
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "initial":
        setup_initial_mods()
    elif len(sys.argv) > 1 and sys.argv[1] == "updated":
        setup_initial_mods()
        setup_updated_mods()