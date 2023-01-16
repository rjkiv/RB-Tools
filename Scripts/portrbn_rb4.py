from pathlib import Path
import sys
import pprint
    
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
                    print(g.name)
                    # if there are harmonies...
                    # else, just stick the mid as is into the output folder
                    output_path.joinpath(g.name).write_bytes(g.read_bytes())
                # rename/move the .mogg
                elif ".mogg" in g.name:
                    output_path.joinpath(f"{shortname_new}.mogg").write_bytes(g.read_bytes())
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
    
    # FIXME: add support for the comments below
    # for the purposes of RB3DX, if harmonies are found in the RB4 mid, make an _update.mid and a line for missing_songs.dta, and put these in another folder titled "RB3DX"
    # AND delete the harmonies from the "output" mid
    
    # the _update.mid should contain pro drums and harms
    
if __name__ == "__main__":
    main()
