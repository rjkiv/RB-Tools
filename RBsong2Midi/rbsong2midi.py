import math
import os
import struct
import sys

from mido import Message, MetaMessage, MidiFile, MidiTrack
from mido import merge_tracks


class venueItem:
    def __init__(self, time, event):
        self.time = time
        self.event = event


class consoleType:
    def __init__(self, console):
        if console == '360':
            self.endian = 'big'
            self.pack = '>f'
        else:
            self.endian = 'little'
            self.pack = '<f'


console = consoleType('PS4')
tpb = 480

# All venue anim parts have 13 unknown bytes after them (always seems to be 13)
# Format: 1 byte, 4 bytes, 4 bytes, 4 bytes
# 4 bytes after these 13 are the first event

animParts = {
    'bass_intensity': b'bass_intensity',
    'guitar_intensity': b'guitar_intensity',
    'drum_intensity': b'drum_intensity',
    'mic_intensity': b'mic_intensity',
    'keyboard_intensity': b'keyboard_intensity',
    'shot_bg': b'shot_bg',
    'shot_bk': b'shot_bk',
    'shot_gk': b'shot_gk',
    'shot_5': b'shot_5',
    'crowd': b'\x05crowd',
    'postproc': b'postproc_interp',
    'fog': b'stagekit_fog',
    'lights': b'lightpreset_interp',
    'keyframe': b'lightpreset_keyframe_interp',
    'spot_guitar': b'spot_guitar',
    'spot_bass': b'spot_bass',
    'spot_drums': b'spot_drums',
    'spot_vocal': b'spot_vocal',
    'spot_keyboard': b'spot_keyboard',
    'part2_sing': b'part2_sing',
    'part3_sing': b'part3_sing',
    'part4_sing': b'part4_sing',
    'world_event': b'world_event'
}

playerAnim = ['bass_intensity',
              'guitar_intensity',
              'drum_intensity',
              'mic_intensity',
              'keyboard_intensity'
              ]

lights = ['lightpreset',
          'lightpreset_keyframe',
          'world_event',
          'spot_guitar',
          'spot_bass',
          'spot_drums',
          'spot_vocal',
          'part2_sing',
          'part3_sing',
          'part4_sing']

separate = ['postproc',
            'shot_bg',
            'crowd',
            'stagekit_fog']

rest = ['shot_5',  # Potentially for the future
        'spot_keyboard',
        'shot_bk',
        'shot_gk',
        ]

oneVenueTrack = ['lightpreset', 'lightpreset_keyframe', 'world_event', 'spot_guitar', 'spot_bass', 'spot_drums', 'spot_keyboard',
            'spot_vocal', 'part2_sing', 'part3_sing', 'part4_sing', 'postproc', 'shot_bg']

oneVenueSep = ['crowd', 'stagekit_fog']

dataToPull = oneVenueTrack + oneVenueSep

ppDic = {
    'profilm_a': 'ProFilm_a',
    'profilm_b': 'ProFilm_b',
    'profilm_mirror_a': 'ProFilm_mirror_a',
    'profilm_psychedelic_blue_red': 'ProFilm_psychedelic_blue_red'

}


def readFourBytes(anim, start):
    x = []
    for y in range(4):  # Iterate through the 4 bytes that make up the starting number
        x.append(anim[start])
        start += 1
    xBytes = bytearray(x)
    x = int.from_bytes(xBytes, console.endian)
    return x, xBytes, start

def readSixteenBytes(anim, start):
    x = []
    for y in range(16):  # Iterate through the 16 bytes to determine rbsong type
        x.append(chr(anim[start]))
        start += 1
    check = ''.join(x)
    if check == "hidden_in_editor":
        return True
    else:
        return False


def defaultMidi():
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)
    track.append(MetaMessage('set_tempo', tempo=500000, time=0))
    track.append(MetaMessage('time_signature', numerator=4, denominator=4, time=0))
    return mid

def pullEventName(anim, start):
    eventname_loc = b'RBVenueAuthoring'
    eventstart = anim.find(eventname_loc, start) + len(eventname_loc) + 12
    animNameLen, animNameLenByte, eventstart = readFourBytes(anim, eventstart)

    animName = []
    for y in range(animNameLen):
        animName.append(chr(anim[eventstart]))
        eventstart += 1
    animName = ''.join(animName)
    #exit()
    return animName


def pullData(anim, start, beat):
    start_loc = b'driven_prop'
    start = anim.find(start_loc, start) + len(start_loc) + 4
    animName = pullEventName(anim, start)
    if animName not in dataToPull:
        return -1, -1, start
    events, eventsByte, start = readFourBytes(anim, start)
    if readSixteenBytes(anim, start):
        start += 43
        events, eventsByte, start = readFourBytes(anim, start)

    eventsList = []
    for x in range(events):
        time, timeByte, start = readFourBytes(anim, start)
        eventLen, eventLenByte, start = readFourBytes(anim, start)
        event = []
        for y in range(eventLen):
            event.append(chr(anim[start]))
            start += 1
        if not event:
            if not eventsList:
                eventsList = -1
            else:
                event = eventsList[-1].event
        else:
            event = ''.join(event)
            if event in ppDic:
                event = ppDic[event]
        if eventsList != -1:
            roundFloat = round(struct.unpack(console.pack, timeByte)[0], 3)
            splitFloat = math.modf(roundFloat)
            try:
                nextBeatTicks = beat[int(splitFloat[1]) + 1] - beat[int(splitFloat[1])]
                timeFromBeat = round(nextBeatTicks * splitFloat[0])
                timeInSong = beat[int(splitFloat[1])] + timeFromBeat
                eventsList.append(venueItem(timeInSong, event))
            except:
                continue

    #print(animName)
    return eventsList, animName, start


def parseData(eventsDict, mid, oneVenue):
    if oneVenue:
        combined = oneVenueTrack
        sep = oneVenueSep
    else:
        combined = lights
        sep = separate
    toMerge = []
    for tracks in combined:
        if tracks in eventsDict:
            if eventsDict[tracks] != -1:
                timeStart = 0
                tempTrack = MidiTrack()
                prevType = 'note_off'
                for y, x in enumerate(eventsDict[tracks]):
                    timeVal = x.time - timeStart
                    noteVal = 0
                    if tracks.endswith('_sing') or tracks.startswith('spot_'):
                        if tracks.endswith('_sing'):
                            if tracks.startswith('part2'):
                                noteVal = 87
                            elif tracks.startswith('part3'):
                                noteVal = 85
                            elif tracks.startswith('part4'):
                                noteVal = 86
                            else:
                                print(f"Unknown singalong event found at {x.time}")
                                exit()
                        if tracks.startswith('spot_'):
                            if tracks.endswith('keyboard'):
                                noteVal = 41
                            elif tracks.endswith('vocal'):
                                noteVal = 40
                            elif tracks.endswith('guitar'):
                                noteVal = 39
                            elif tracks.endswith('drums'):
                                noteVal = 38
                            elif tracks.endswith('bass'):
                                noteVal = 37
                            else:
                                print(f"Unknown spotlight event found at {x.time}")
                                exit()
                        if x.event.endswith('on'):
                            if prevType == 'note_on':
                                tempTrack.append(Message('note_off', note=noteVal, velocity=0, time=timeVal))
                                timeStart = x.time
                                tempTrack.append(Message('note_on', note=noteVal, velocity=100, time=0))
                            else:
                                tempTrack.append(Message('note_on', note=noteVal, velocity=100, time=timeVal))
                            prevType = 'note_on'
                        elif x.event.endswith('off'):
                            tempTrack.append(Message('note_off', note=noteVal, velocity=0, time=timeVal))
                            prevType = 'note_off'
                        else:
                            print(f"Unknown state event found at {x.time}")
                            exit()
                    else:
                        if tracks == 'lightpreset':
                            textEvent = f'[lighting ({x.event})]'
                        elif tracks == 'postproc':
                            textEvent = f'[{x.event}.pp]'
                        else:
                            textEvent = x.event
                            if textEvent.startswith('band'):
                                textEvent = f'coop{textEvent[4:]}'
                            if textEvent.endswith('crowd') and not textEvent.startswith('directed'):
                                textEvent = textEvent[:-5]+'behind'
                            if textEvent.endswith('near_head'):
                                textEvent = textEvent[:-9]+'closeup'
                            textEvent = f'[{textEvent}]'
                        tempTrack.append(MetaMessage('text', text=textEvent, time=timeVal))
                    timeStart = x.time
                toMerge.append(tempTrack)
    mid.tracks.append(merge_tracks(toMerge))
    if combined == oneVenueTrack:
        mid.tracks[-1].name = "VENUE"
    else:
        mid.tracks[-1].name = "lights"
    for tracks in sep:
        if tracks in eventsDict:
            if eventsDict[tracks] != -1:
                tname = tracks
                mid.add_track(name=tname)
                timeStart = 0
                for y, x in enumerate(eventsDict[tracks]):
                    """mapLower = beat[beat <= x.time].max()
                    if tracks == 'shot_bg':
                        print(mapLower, x.time)"""
                    timeVal = x.time - timeStart
                    if tracks == 'stagekit_fog':
                        textEvent = f'[Fog{x.event.capitalize()}]'
                    elif tracks == 'postproc':
                        textEvent = f'[{x.event}.pp]'
                    else:
                        textEvent = f'[{x.event}]'
                    mid.tracks[-1].append(MetaMessage('text', text=textEvent, time=timeVal))
                    timeStart = x.time
    return mid


def grabBeatTrack(mid):
    beatNotes = []
    time = 0
    for tracks in mid.tracks:
        if tracks.name == "BEAT":
            for msg in tracks:
                time += msg.time
                if msg.type == "note_on":
                    beatNotes.append(time)
    beatNotes.append(beatNotes[-1] + tpb)

    return beatNotes


def main(anim, mid, output, oneVenue):
    beat = grabBeatTrack(mid)
    start = 0
    eventTotal = anim.count(b'driven_prop')
    #print(eventTotal)
    eventsDict = {}
    for x in range(eventTotal):
        events, eventsName, start = pullData(anim, start, beat)
        #print(eventsName)
        eventsDict[eventsName] = events
    mid = parseData(eventsDict, mid, oneVenue)
    mid.save(filename=f'{output}_venue.mid')


if __name__ == "__main__":

    if len(sys.argv) == 1:
        print(
            "No file found. Please run this script with a \".rbsong\" file and a MIDI file to merge together")
        input("Press any key to exit")
        exit()
    if sys.argv[1].endswith(".rbsong"):
        with open(sys.argv[1], "rb") as f:
            anim = f.read()
        try:
            mid = MidiFile(os.path.splitext(sys.argv[1])[0] + '.mid')
        except:
            print("No midi file found. It must be located in the same folder as your rbsong file.")
            input("Press any key to exit")
            exit()
    else:
        print("No rbsong file found.")
        input("Press any key to exit")
        exit()
    output = os.path.splitext(sys.argv[1])[0]
    if 'separate' in sys.argv:
        oneVenue = False
    else:
        oneVenue = True
    main(anim, mid, output, oneVenue)
