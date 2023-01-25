from pathlib import Path
from mido import MidiFile
import sys
import pprint

OVERDRIVE_NOTE = 116

# FIXME: account for 8th note time signatures (6/8, 7/8, etc)
# clean this code up so it's not gross
def iterate_tracks(mid: Path):
    print(mid)
    song = MidiFile(mid)
    time_signatures = {}
    for track in song.tracks:
        print(track.name)
        if track.name == f"{mid.stem}":
            total_time = 0
            ticks_per_measure = song.ticks_per_beat * 4
            measure = 1
            beat = 1
            ticks = 0
            for msg in track:
                # get M:B:T from delta time
                measure += int(msg.time / (ticks_per_measure))
                beat += int((msg.time % ticks_per_measure) / song.ticks_per_beat)
                ticks += (msg.time % ticks_per_measure) % song.ticks_per_beat
                if ticks >= song.ticks_per_beat:
                    beat += int((ticks / song.ticks_per_beat))
                    ticks = int(ticks % song.ticks_per_beat)
                if beat > (ticks_per_measure / song.ticks_per_beat):
                    measure += int(beat / (ticks_per_measure / song.ticks_per_beat))
                    beat = int(beat % (ticks_per_measure / song.ticks_per_beat))
                total_time += msg.time
                if msg.type == "time_signature":
                    ticks_per_measure = song.ticks_per_beat * msg.numerator
                    time_signatures[total_time] = {}
                    time_signatures[total_time]["numerator"] = msg.numerator
                    time_signatures[total_time]["denominator"] = msg.denominator
                    if beat > 1:
                        measure += 1
                        beat = 1
                        ticks = 0
                print(f"time {total_time:07d} and M:B:T {measure:03d}:{beat:02d}:{ticks:03d} - {msg}")
            print(time_signatures)
        elif track.name == "PART DRUMS":
            total_time = 0
            ticks_per_measure = song.ticks_per_beat * time_signatures[0]["numerator"]
            measure = 1
            beat = 1
            ticks = 0
            for msg in track:
                # get M:B:T from delta time
                measure += int(msg.time / (ticks_per_measure))
                beat += int((msg.time % ticks_per_measure) / song.ticks_per_beat)
                ticks += (msg.time % ticks_per_measure) % song.ticks_per_beat
                if ticks >= song.ticks_per_beat:
                    # if measure < 15:
                    #     print(f"adding {ticks / song.ticks_per_beat} to beat {beat}")
                    beat += int((ticks / song.ticks_per_beat))
                    ticks = int(ticks % song.ticks_per_beat)
                if beat > (ticks_per_measure / song.ticks_per_beat):
                    # if measure < 15:
                    #     print(f"beat = {beat}, which is > {ticks_per_measure / song.ticks_per_beat}")
                    measure += int(beat / (ticks_per_measure / song.ticks_per_beat))
                    beat = int(beat % (ticks_per_measure / song.ticks_per_beat))
                total_time += msg.time
                if total_time in time_signatures:
                    # print(f"total_time {total_time} found in time_signatures")
                    ticks_per_measure = song.ticks_per_beat * int(time_signatures[total_time]["numerator"])
                    if beat > 1:
                        measure += 1
                        beat = 1
                        ticks = 0
                print(f"time {total_time:07d} and M:B:T {measure:03d}:{beat:02d}:{ticks:03d} - {msg}")

def main():
    if len(sys.argv) != 2:
        print("no mid provided")
        exit()
    iterate_tracks(Path().absolute().joinpath(sys.argv[1]))
    
if __name__ == "__main__":
    main()
