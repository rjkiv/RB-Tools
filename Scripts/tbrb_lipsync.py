from pathlib import Path
from mido import MidiFile, MidiTrack, MetaMessage, Message
import sys

# take a midi track, convert its text events to midi notes
# and return a new track
def convert_text_to_notes(track: MidiTrack, note: int):
    time = 0
    initial_track_list = []
    for msg in track:
        time += msg.time
        initial_track_list.append((time, msg))
    
    new_track_list = []
    for idx in range(len(initial_track_list)):
        # append track name as normal
        the_tuple = initial_track_list[idx]
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
                new_track_list.append((the_tuple[0], Message("note_on", channel=channel, note=note, velocity=velocity, time=0)))
                new_track_list.append((the_tuple[0] + 60, Message("note_off", channel=channel, note=note, velocity=velocity, time=0)))
            else:
                # sort the new track list, and examine everything that comes after the_tuple
                new_track_list.sort(key=lambda a: a[0])
                zero_index = new_track_list.index(the_tuple)
                for i in range(zero_index+1, len(new_track_list)):
                    new_track_list[i] = (the_tuple[0], new_track_list[i][1])
    new_track_list.sort(key=lambda a: a[0])
    
    new_track = MidiTrack()
    new_track.append(MetaMessage("track_name", name="AUDREY", time=0))

    for i in range(1, len(new_track_list)):
        # text event
        if type(new_track_list[i][1]) == MetaMessage:
            new_track.append(MetaMessage("text", text=(new_track_list[i][1].text.replace("r_lids", "Blink")), time=new_track_list[i][0] - new_track_list[i-1][0]))
        # note event
        elif type(new_track_list[i][1]) == Message:
            new_track.append(Message(new_track_list[i][1].type, channel=new_track_list[i][1].channel, note=new_track_list[i][1].note, velocity=new_track_list[i][1].velocity, time=new_track_list[i][0] - new_track_list[i-1][0]))
    new_track.append(MetaMessage("end_of_track"))
    return new_track

def process_tbrb_mid(mid_path: Path):
    print(mid_path)
    mid = MidiFile(mid_path)
    new_mid = MidiFile()
    for track in mid.tracks:
        print(track.name)
        if track.name == "part1-R_lids": # if you want to change the midi track being processed, write its name here...
            new_mid.tracks.append(convert_text_to_notes(track, 51)) # and change the corresponding midi note
        else:
            new_mid.tracks.append(track)

    new_mid.save("out.mid")

def main():
    if len(sys.argv) != 2:
        print("no mid provided")
        exit()
    process_tbrb_mid(sys.argv[1])
    
if __name__ == "__main__":
    main()
