from pathlib import Path
from mido import MidiFile, MidiTrack, MetaMessage, Message
import sys
import pprint

def step_one(mid_path: Path):
    print(mid_path)
    mid = MidiFile(mid_path)
    new_mid = MidiFile()
    for track in mid.tracks:
        print(track.name)
        if track.name == "part1-R_lids":
            time = 0
            track_list = []
            # get initial track list
            for msg in track:
                time += msg.time
                # print(f"{time:07d} {msg}")
                track_list.append((time, msg))

            # track_list.append((20, "asdf"))
            new_track_list = []

            for idx in range(len(track_list)):
                the_tuple = track_list[idx]
                # just append track name as normal
                if the_tuple[1].type == "track_name":
                    new_track_list.append(the_tuple)
                # if text event
                elif the_tuple[1].type == "text":
                    # append this text event
                    new_track_list.append(the_tuple)
                    # if this text event is NOT 0 hold
                    hold_num = int(the_tuple[1].text.split()[1])
                    if hold_num != 0:
                        channel = int(hold_num / 128)
                        velocity = int(hold_num / (channel + 1))
                        # Message('note_on', channel=0, note=100, velocity=3, time=6.2)
                        
                        new_track_list.append((the_tuple[0], Message("note_on", channel=channel, note=51, velocity=velocity, time=0)))
                        new_track_list.append((the_tuple[0] + 60, Message("note_off", channel=channel, note=51, velocity=velocity, time=0)))
                    else:
                        # sort the new track list, and examine everything that comes after the_tuple
                        new_track_list.sort(key=lambda a: a[0])
                        zero_index = new_track_list.index(the_tuple)
                        for i in range(zero_index+1, len(new_track_list)):
                            new_track_list[i] = (the_tuple[0], new_track_list[i][1])

            new_track_list.sort(key=lambda a: a[0])

            for x in new_track_list:
                print(x)

            new_track = MidiTrack()
            new_track.append(new_track_list[0][1])
            for idx in range(1, len(new_track_list)):
                if type(new_track_list[idx][1]) == MetaMessage:
                    new_track.append(MetaMessage("text", text=new_track_list[idx][1].text, time=new_track_list[idx][0] - new_track_list[idx-1][0]))
                elif type(new_track_list[idx][1]) == Message:
                    new_track.append(Message(new_track_list[idx][1].type, channel=new_track_list[idx][1].channel, note=new_track_list[idx][1].note, velocity=new_track_list[idx][1].velocity, time=new_track_list[idx][0] - new_track_list[idx-1][0]))
                # print(f"{new_track_list[idx][0]}: {new_track_list[idx][1]} at time {new_track_list[idx][0] - new_track_list[idx-1][0]}")
            new_track.append(MetaMessage("end_of_track"))
            new_mid.tracks.append(new_track)
        else:
            new_mid.tracks.append(track)

        new_mid.save("out.mid")

def main():
    if len(sys.argv) != 2:
        print("no mid provided")
        exit()
    step_one(sys.argv[1])
    
if __name__ == "__main__":
    main()
