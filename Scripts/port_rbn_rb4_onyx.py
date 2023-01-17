from pathlib import Path
from mido import MidiFile, MidiTrack
import sys
import pprint
import subprocess

# NOTES REGARDING ONYX CLI SYNTAX:
# Onyx location on Windows: C:/Program Files/OnyxToolkit/onyx.exe
# To take file/folder contents and put them into a CON:
# onyx stfs my_folder --to new_con_name --game (either rb3 or rb2)
# To take a CON and extract its contents:
# onyx extract my_con_name --to my_output_directory

# use pathlib's Path.replace and Path.rename functions when renaming/replacing files in-place
  
def onyx_extract_con_files(con_name):
    # print("hello from onyx extract con files")
    cmd_extract = f"C:/Program Files/OnyxToolkit/onyx extract {con_name}".split()
    subprocess.run(cmd_extract)

def onyx_pack_files_into_con(folder_name, new_con_name):
    # print("hello from onyx pack files into con")
    cmd_pack = f"C:/Program Files/OnyxToolkit/onyx stfs {folder_name} --to {new_con_name} --game rb2".split()
    subprocess.run(cmd_pack)

def rm_tree(pth):
    pth = Path(pth)
    for child in pth.glob('*'):
        if child.is_file():
            child.unlink()
        else:
            rm_tree(child)
    pth.rmdir()

def browse_extracted_folders(extracted_folder_name):
    cwd = Path().absolute()

    # get RB4 shortname
    for root_file in cwd.glob("*.mid"):
        shortname_new = root_file.stem
        break

    # if there are harms present in the RB4 file, remove them and place them in an _update mid
    
    root_of_con = cwd.joinpath(f"{extracted_folder_name}/songs")

    remove_from_rb4_mid = []
    rb4_mid = MidiFile(cwd.joinpath(f"{shortname_new}.mid"))
    update_mid = MidiFile()
    harms_in_mid = False
    for track in rb4_mid.tracks:
        if "HARM" in track.name:
            harms_in_mid = True
            break

    if harms_in_mid:
        for track in rb4_mid.tracks:
            if track.name == shortname_new:
                update_mid.add_track()
                update_mid.tracks[-1] = track.copy()
            elif track.name == "PART DRUMS":
                update_mid.add_track()
                update_mid.tracks[-1] = track.copy()
            elif "HARM" in track.name:
                update_mid.add_track()
                update_mid.tracks[-1] = track.copy()
                remove_from_rb4_mid.append(track)
        for track in remove_from_rb4_mid:
            rb4_mid.tracks.remove(track)

        rb4_mid.save(cwd.joinpath(f"{shortname_new}.mid"))
        update_mid.save(cwd.joinpath(f"{shortname_new}_update.mid"))

    # get original shortname and songs
    for f in root_of_con.glob("*"):
        if f.name == "songs.dta":
            with open(root_of_con.joinpath(f"{f.name}"), "r", encoding="ISO-8859-1") as ff:
                song_dta = [line for line in ff.readlines()]
        elif "UGC" in f.name:
            shortname_ugc = f.name
            f.rename(root_of_con.joinpath(shortname_new))
    
    print(f"Old shortname: {shortname_ugc}")
    print(f"New shortname: {shortname_new}")

    # midi/mogg/gen directory now
    mid_dir = root_of_con.joinpath(shortname_new)
    for g in mid_dir.glob("*"):
        if g.suffix == ".mogg":
            g.rename(mid_dir.joinpath(f"{shortname_new}.mogg"))
        elif g.suffix == ".mid":
            cwd.joinpath(f"{shortname_new}.mid").replace(g).rename(mid_dir.joinpath(f"{shortname_new}.mid"))

    # milo/png/weights directory now
    milo_dir = mid_dir.joinpath("gen")
    for h in milo_dir.glob("*"):
        the_new_filename = h.stem.replace(shortname_ugc, shortname_new)
        h.rename(milo_dir.joinpath(f"{the_new_filename}{h.suffix}"))

    # edit and overwrite the original songs.dta
    for i in range(len(song_dta)):
        if shortname_ugc in song_dta[i]:
            song_dta[i] = song_dta[i].replace(shortname_ugc, shortname_new)
        if "'rating' 4" in song_dta[i]:
            song_dta[i] = song_dta[i].replace("4", "2")
    
    with open(root_of_con.joinpath("songs.dta"),"w",encoding="ISO-8859-1") as dta_output:
        dta_output.writelines(song_dta)

def main():
    # To port a RBN 1.0 CON for use in RB3, with an additional RB4 mid:
    # Place the original 1.0 CON and the new RB4 mid in the same directory as this script,
    # and it will output a new, updated CON.

    # pass in name of CON you want to extract from
    if len(sys.argv) != 2:
        print("no CON name provided")
        exit()
    else:
        con_name = sys.argv[1].replace(".\\","")
    onyx_extract_con_files(con_name)
    browse_extracted_folders(f"{con_name}_extract")

    output_con_name = con_name.replace("_","") + "-Updated"

    onyx_pack_files_into_con(f"{con_name}_extract", output_con_name)

    print(f"RB3-friendly {output_con_name} CON has been created.")
    
if __name__ == "__main__":
    main()
