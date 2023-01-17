from pathlib import Path
from mido import MidiFile, MidiTrack
import sys
import pprint

# NOTES REGARDING ONYX CLI SYNTAX:
# Onyx location on Windows: C:/Program Files/OnyxToolkit/onyx.exe
# To take file/folder contents and put them into a CON:
# onyx stfs my_folder --to new_con_name --game (either rb3 or rb2)
    
def port_rbn(shortname: str):
    print("hello from port_rbn")
    print(shortname)
    cwd = Path().absolute()
    for f in cwd.glob("songs/*"):
        print(f)
        
def port_rbn_rb4():
    print("hello from port_rbn, rb4 edition")
    cwd = Path().absolute()
    cwd.joinpath("output").mkdir(parents=True, exist_ok=True)
    output_path = cwd.joinpath("output")
    for f in cwd.glob("songs/*"):
        # songs.dta: read in the dta and save contents to a list
        if f.name == "songs.dta":
            with open(cwd.joinpath(f"songs/{f.name}"), "r", encoding="ISO-8859-1") as ff:
                song_dta = [line for line in ff.readlines()]
        else:
            shortname_ugc = f.name
            # obtain new shortname from the RB4 mid
            for asdf in cwd.glob(f"songs/{shortname_ugc}/*"):
                if ".mid" in asdf.name and shortname_ugc not in asdf.name:
                    shortname_new = asdf.stem
                    break
            for g in cwd.glob(f"songs/{shortname_ugc}/*"):
                if shortname_new in g.name:
                    harms_in_mid = False
                    mid = MidiFile(g)
                    for track in mid.tracks:
                        if "HARM" in track.name:
                            harms_in_mid = True
                            break
                    # if there are harmonies:
                    if harms_in_mid:
                        # create two mids:
                            # the first is the original RB4 mid but with harms removed
                            # the second is just pro drums and harms, meant to be an _update.mid file
                            mid_for_con = mid
                            remove_from_con_mid = []
                            mid_for_update = MidiFile()
                            for track in mid_for_con.tracks:
                                if track.name == shortname_new: # the tempo map
                                    mid_for_update.add_track()
                                    mid_for_update.tracks[-1] = track.copy()
                                elif track.name == "PART DRUMS":
                                    mid_for_update.add_track()
                                    mid_for_update.tracks[-1] = track.copy()
                                elif "HARM" in track.name:
                                    mid_for_update.add_track()
                                    mid_for_update.tracks[-1] = track.copy()
                                    remove_from_con_mid.append(track)
                            for track in remove_from_con_mid:
                                mid_for_con.tracks.remove(track)
                                
#                            # just to verify that the two mids check out:
#                            print("new RB4 mid:")
#                            for track in mid_for_con.tracks:
#                                print(track.name)
#                            print("\nupdate mid:")
#                            for track in mid_for_update.tracks:
#                                print(track.name)
                                
                            mid_for_con.save(output_path.joinpath(f"{shortname_new}.mid"))
                            mid_for_update.save(output_path.joinpath(f"{shortname_new}_update.mid"))
                            print("base and update mids created")
                            
                    # else, just stick the mid as is into the output folder
                    else:
                        output_path.joinpath(g.name).write_bytes(g.read_bytes())
                        print("base mid created")
                # rename/move the .mogg
                elif ".mogg" in g.name:
                    output_path.joinpath(f"{shortname_new}.mogg").write_bytes(g.read_bytes())
                    print(f"{g.name} --> {shortname_new}.mogg")
                # rename/move the .milo/.png/weights files
                elif g.name == "gen":
                    for h in cwd.glob(f"songs/{shortname_ugc}/gen/*"):
                        the_new_filename = h.name.replace(shortname_ugc, shortname_new)
                        print(f"{h.name} --> {the_new_filename}")
                        output_path.joinpath(the_new_filename).write_bytes(h.read_bytes())
    # now, edit the songs.dta
    for i in range(len(song_dta)):
        if shortname_ugc in song_dta[i]:
            song_dta[i] = song_dta[i].replace(shortname_ugc, shortname_new)
        if "'rating' 4" in song_dta[i]:
            song_dta[i] = song_dta[i].replace("4", "2")

    # and move the new songs.dta to the output folder
    with open(output_path.joinpath("songs.dta"), "w", encoding="ISO-8859-1") as dta_output:
        dta_output.writelines(song_dta)

def main():
    # To port a RBN 1.0 CON for use in RB3, with an additional RB4 mid:
    # Pass in the "songs" folder that you extracted using C3 CON Tools
    # and stick the corresponding RB4 song mid in the same folder as the original song's mid,
    # and the script will create an "output" folder containing the updated files to create a new CON with.
    port_rbn_rb4()
    
if __name__ == "__main__":
    main()
