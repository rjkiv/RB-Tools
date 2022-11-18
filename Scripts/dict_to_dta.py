from pathlib import Path
import sys
import pprint
import json
import re

# removes any comments from a RB dta, and then returns a nice, tokenized list to parse
def clean_dta(dta_path: Path) -> list:
    with open(dta_path, encoding="latin1") as f:
        lines = [line.lstrip() for line in f]
    reduced_lines = [x.split(";",1)[0] for x in lines]
    dta_as_str = ''.join(reduced_lines)
    dta_as_list = dta_as_str.replace("("," ( ").replace(")"," ) ").split()
    return dta_as_list

# parse, read_from_tokens, and atom have all been originally written by Peter Norvig
# parse and atom have been tweaked for the purposes of parsing RB dtas
# explanations of his functions can be found here: http://norvig.com/lispy.html
def parse(program: list):
    "Read a Scheme expression from a string."
    program.insert(0, "(")
    program.append(")")
    return read_from_tokens((program))
    
def read_from_tokens(tokens: list):
    "Read an expression from a sequence of tokens."
    if len(tokens) == 0:
        raise SyntaxError('unexpected EOF')
    token = tokens.pop(0)
    if token == '(':
        L = []
        while tokens[0] != ')':
            L.append(read_from_tokens(tokens))
        tokens.pop(0) # pop off ')'
        return L
    elif token == ')':
        raise SyntaxError('unexpected )')
    else:
        return atom(token)
        
def atom(token: str):
    "Numbers become numbers; every other token is a symbol."
    try: return int(token)
    except ValueError:
        try: return float(token)
        except ValueError:
            return (str(token)).strip("'").strip('"')
            
# clean up name entry in case there are parentheses in the song title (i.e. (Don't Fear) The Reaper)
def dict_from_name(parsed_name) -> str:
    new_song_name_list = []
    for s in range(len(parsed_name)):
        if s > 0:
            if type(parsed_name[s]) == list:
                new_song_name_list.append("(" + " ".join(parsed_name[s]) + ")")
            elif parsed_name[s] != "":
                new_song_name_list.append(str(parsed_name[s]))
    return " ".join(new_song_name_list)
        
# parse song part difficulties and return a dict
def dict_from_rank(parsed_rank: list):
    rank_dict = {}
    for rank in parsed_rank:
        if type(rank) == list:
            rank_dict[rank[0]] = rank[1]
    return rank_dict

# parse song info (pans, vols, etc) and return a dict
def dict_from_song(parsed_song: list):
    song_info_dict = {}
    for info in parsed_song:
        if type(info) == list:
            if "drum_" in info[0]:
                song_info_dict[info[0]] = {}
                song_info_dict[info[0]][info[1][0]] = info[1][1]
            elif info[0] == "tracks":
                song_info_dict[info[0]] = {}
                for instr_tracks in info[1]:
                    song_info_dict[info[0]][instr_tracks[0]] = instr_tracks[1] if type(instr_tracks[1]) == list else [instr_tracks[1]]
            elif info[0] == "crowd_channels":
                song_info_dict[info[0]] = info[1:]
            else:
                song_info_dict[info[0]] = info[1]
    return song_info_dict
            
# convert the list of lists that parse returns into a big song dictionary
def dict_from_parsed(parsed: list):
    big_songs_dict = {}
    big_songs_dict["songs"] = {}
    song_dict = big_songs_dict["songs"]
    for song in parsed:
        for a in range(len(song)):
            if a == 0: # the shortname
                song_dict[song[0]] = {}
            elif song[a][0] == "name":
                song_dict[song[0]]["name"] = dict_from_name(song[a])
            elif song[a][0] == "song":
                song_dict[song[0]]["song"] = dict_from_song(song[a])
            elif song[a][0] == "rank":
                song_dict[song[0]]["rank"] = dict_from_rank(song[a])
            else:
                val = []
                for b in range(len(song[a])):
                    if b == 0:
                        key = song[a][b]
                    else:
                        val.append(song[a][b])
                if all(isinstance(item, str) for item in val):
                    song_dict[song[0]][key] = (" ".join(x for x in val)).strip('"')
                else:
                    song_dict[song[0]][key] = val if len(val) > 1 else val[0]
                    
    return big_songs_dict

# the main parse function - supply a path to a dta, and it will return a big song dictionary
def parse_dta(dta_path: Path):
    print(dta_path)
    parsed = parse(clean_dta(dta_path))
    parsed_dta_dict = dict_from_parsed(parsed)
    pprint.pprint(parsed_dta_dict, sort_dicts=False)
    return parsed_dta_dict

def dict_to_dta(song_dict: dict):
    # FIXME: shorten this block of code to something like a recursive function
    res = []
    for k in song_dict.keys():
        res.append([k])
        if isinstance(song_dict[k], dict):
            for kk in song_dict[k].keys():
                res[-1].append([kk])
                if isinstance(song_dict[k][kk], dict):
                    for kkk in song_dict[k][kk].keys():
                        res[-1][-1].append([kkk])
                        if isinstance(song_dict[k][kk][kkk], dict):
                            for kkkk in song_dict[k][kk][kkk].keys():
                                res[-1][-1][-1].append([kkkk])
                                if isinstance(song_dict[k][kk][kkk][kkkk], dict):
                                    pass
                                else:
                                    res[-1][-1][-1][-1].append(song_dict[k][kk][kkk][kkkk])
                        else:
                            res[-1][-1][-1].append(song_dict[k][kk][kkk])
                else:
                    res[-1][-1].append(song_dict[k][kk])
        else:
            res.append(song_dict[k])
                
    # FIXME: add proper indenting and spacing to the output dta
    output = []
    def removeNestings(l):
        for i in l:
            if type(i) == list:
                i.insert(0, "(")
                i.append(")")
                removeNestings(i)
            else:
                output.append(i)
                output.append(" ")
                
    removeNestings(res)

    i = 0
    while i < len(output):
        if output[i] == "(" and i > 0:
            output.insert(i, "\n")
            i += 1
        i += 1
        
    print(output)
    
    spaced_output = []
    phrase = []
    for z in output:
        phrase.append(z)
        if z == "\n":
            spaced_output.append(phrase.copy())
            phrase.clear()
    
    indent = 0
    for line in spaced_output:
        print(line)
        
    # FIXME: name, artist, and other attributes that require quotes, NEED QUOTES
    with open("output.dta","w") as f:
        indent = 0
        for x in output:
            f.write(str(x))

def main():
    if len(sys.argv) != 2:
        print("no dta provided")
        exit()
    big_song_dict = parse_dta(sys.argv[1])
    print("Dict to dta...")
    dict_to_dta(big_song_dict["songs"])
    
if __name__ == "__main__":
    main()
