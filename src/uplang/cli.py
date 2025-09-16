import click
import os
from uplang.core import scanner, state, extractor, comparator, synchronizer

@click.group()
def cli():
    """A tool to synchronize language files for Minecraft modpacks."""
    pass

@cli.command()
@click.argument("mods_dir", type=click.Path(exists=True, file_okay=False, resolve_path=True))
@click.argument("resource_pack_dir", type=click.Path(file_okay=False, resolve_path=True))
def init(mods_dir, resource_pack_dir):
    """Initializes the resource pack for the first time."""
    mods_dir = os.path.normpath(mods_dir)
    resource_pack_dir = os.path.normpath(resource_pack_dir)
    print("Initializing resource pack...")
    if not os.path.isdir(resource_pack_dir):
        os.makedirs(resource_pack_dir)

    mods = scanner.scan_mods(mods_dir)
    if not mods:
        print("No mods found to initialize.")
        return

    for mod in mods:
        en_us_extracted = extractor.extract_lang_file(mod, "en_us")
        if en_us_extracted:
            _, en_us_content = en_us_extracted
            target_dir = os.path.join(resource_pack_dir, "assets", mod.mod_id, "lang")
            os.makedirs(target_dir, exist_ok=True)
            
            rp_en_us_path = os.path.join(target_dir, "en_us.json")
            rp_zh_cn_path = os.path.join(target_dir, "zh_cn.json")

            # Write en_us.json to resource pack
            with open(rp_en_us_path, 'wb') as f:
                f.write(en_us_content)

            # Attempt to extract zh_cn.json from mod JAR
            zh_cn_extracted = extractor.extract_lang_file(mod, "zh_cn")
            if zh_cn_extracted:
                _, zh_cn_content = zh_cn_extracted
                # Write zh_cn.json from mod JAR to resource pack
                with open(rp_zh_cn_path, 'wb') as f:
                    f.write(zh_cn_content)
                print(f"  - Copied existing zh_cn.json for {mod.mod_id}")
            else:
                # If no zh_cn.json in mod JAR, copy en_us.json to zh_cn.json
                with open(rp_zh_cn_path, 'wb') as f:
                    f.write(en_us_content)
                print(f"  - Created zh_cn.json from en_us.json for {mod.mod_id}")
            
            # Perform synchronization (completion)
            synchronizer.synchronize_language_file(rp_zh_cn_path, rp_en_us_path)
            
            print(f"Initialized {mod.mod_id}")

    state_file = os.path.join(resource_pack_dir, ".uplang_state.json")
    state.save_state(mods, state_file, mods_dir, resource_pack_dir) # Added mods_dir, resource_pack_dir
    print("\nInitialization complete.")

@cli.command()
@click.argument("mods_dir", type=click.Path(exists=True, file_okay=False, resolve_path=True))
@click.argument("resource_pack_dir", type=click.Path(exists=True, file_okay=False, resolve_path=True))
def check(mods_dir, resource_pack_dir):
    """Checks for mod updates and synchronizes language files."""
    mods_dir = os.path.normpath(mods_dir)
    resource_pack_dir = os.path.normpath(resource_pack_dir)
    state_file = os.path.join(resource_pack_dir, ".uplang_state.json")
    
    print("Loading previous mod state...")
    loaded_state = state.load_state(state_file)
    if not loaded_state:
        print("No previous state found. Please run the 'init' command first.")
        return
    
    old_mods_map = loaded_state.get("mods_map", {})
    
    # Optional: Add checks for consistency of mods_dir and resource_pack_dir
    # For now, we'll just print a warning if they don't match
    if loaded_state.get("project_info", {}).get("mods_directory") != mods_dir:
        print(f"Warning: Mods directory in state file ({loaded_state.get('project_info', {}).get('mods_directory')}) does not match current ({mods_dir}).")
    if loaded_state.get("project_info", {}).get("resource_pack_directory") != resource_pack_dir:
        print(f"Warning: Resource pack directory in state file ({loaded_state.get('project_info', {}).get('resource_pack_directory')}) does not match current ({resource_pack_dir}).")

    print(f"Scanning mods in: {mods_dir}")
    current_mods = scanner.scan_mods(mods_dir)
    current_mods_map = {mod.mod_id: mod for mod in current_mods}
    
    old_mod_ids = set(old_mods_map.keys())
    current_mod_ids = set(current_mods_map.keys())
    
    new_mod_objs = [current_mods_map[mod_id] for mod_id in current_mod_ids - old_mod_ids]
    deleted_mod_objs = [old_mods_map[mod_id] for mod_id in old_mod_ids - current_mod_ids]
    
    updated_mod_objs = []
    for mod_id in old_mod_ids.intersection(current_mod_ids):
        if old_mods_map[mod_id].version != current_mods_map[mod_id].version:
            updated_mod_objs.append(current_mods_map[mod_id])

    # --- Processing Start ---
    if new_mod_objs:
        print("\nProcessing new mods...")
        for mod in new_mod_objs:
            extracted_file = extractor.extract_lang_file(mod, "en_us")
            if extracted_file:
                _, content = extracted_file
                target_dir = os.path.join(resource_pack_dir, "assets", mod.mod_id, "lang")
                os.makedirs(target_dir, exist_ok=True)
                with open(os.path.join(target_dir, "en_us.json"), 'wb') as f:
                    f.write(content)
                with open(os.path.join(target_dir, "zh_cn.json"), 'wb') as f:
                    f.write(content)
                print(f"  - Created language files for new mod: {mod.mod_id}")

    if updated_mod_objs:
        print("\nProcessing updated mods...")
        for mod in updated_mod_objs:
            new_lang_file = extractor.extract_lang_file(mod, "en_us")
            if not new_lang_file:
                continue;

            _, new_content = new_lang_file
            rp_en_us_path = os.path.join(resource_pack_dir, "assets", mod.mod_id, "lang", "en_us.json")
            rp_zh_cn_path = os.path.join(resource_pack_dir, "assets", mod.mod_id, "lang", "zh_cn.json")

            # Always write the new en_us.json
            with open(rp_en_us_path, 'wb') as f:
                f.write(new_content)
            
            # Synchronize zh_cn.json with the newly updated en_us.json
            synchronizer.synchronize_language_file(rp_zh_cn_path, rp_en_us_path)

    # --- Full Language File Synchronization ---
    print("\n--- Synchronizing all language files ---")
    for mod in current_mods:
        rp_en_us_path = os.path.join(resource_pack_dir, "assets", mod.mod_id, "lang", "en_us.json")
        rp_zh_cn_path = os.path.join(resource_pack_dir, "assets", mod.mod_id, "lang", "zh_cn.json")
        synchronizer.synchronize_language_file(rp_zh_cn_path, rp_en_us_path)

    # --- Reporting Start ---
    print("\n--- Mod Change Report ---")
    if not any([new_mod_objs, deleted_mod_objs, updated_mod_objs]):
        print("No changes detected.")
    else:
        if new_mod_objs:
            print(f"\nFound {len(new_mod_objs)} new mods:")
            for mod in new_mod_objs:
                print(f"  - {mod.mod_id} ({mod.version})")
        
        if updated_mod_objs:
            print(f"\nFound {len(updated_mod_objs)} updated mods:")
            for mod in updated_mod_objs:
                print(f"  - {mod.mod_id} (v{old_mods_map[mod.mod_id].version} -> v{mod.version})")

        if deleted_mod_objs:
            print(f"\nFound {len(deleted_mod_objs)} deleted mods:")
            for mod in deleted_mod_objs:
                print(f"  - {mod.mod_id} ({mod.version})")
    print("-------------------------\n")

    state.save_state(current_mods, state_file, mods_dir, resource_pack_dir) # Added mods_dir, resource_pack_dir
    print("Done.")

if __name__ == '__main__':
    cli()