import struct
import sys
import os
import time
from bisect import bisect_left
import numpy as np
from mido import Message, MetaMessage, MidiFile, MidiTrack
from mido import merge_tracks
from mido import second2tick as s2t
from mido import tick2second as t2s


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


class tempoMapItem:
    def __init__(self, time, tempo, avgTempo):
        self.time = time
        self.tempo = tempo
        self.avgTempo = avgTempo  # Avg Tempo up to that point


class tickSecond:
    def __init__(self, tick, second):
        self.tick = tick
        self.second = second


console = consoleType('360')
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

lights = ['lights',
          'keyframe',
          'world_event',
          'spot_guitar',
          'spot_bass',
          'spot_drums',
          'spot_keyboard',
          'spot_vocal',
          'part2_sing',
          'part3_sing',
          'part4_sing']

separate = ['postproc',
            'shot_bg',
            'shot_bk',
            'shot_gk',
            'crowd',
            'fog']

rest = ['shot_5']


def rollingAverage(x, y, z, a):  # x = prevTime, y = curTime, z = avgTempo, a = curTempo
    newTempo = ((x / y) * z) + (a * (y - x) / y)
    return newTempo


def returnSeconds(avgTick, avgTempo, tick, tempo):
    seconds = t2s(avgTick, tpb, avgTempo) + t2s(tick, tpb, tempo)
    return seconds


def tempMap(mid):
    x = []  # Tempo changes
    z = []  # Ticks of tempo changes
    y = 0  # Event counter
    totalTime = 0  # Cumulative total time
    avgTempo = 0
    for msg in mid.tracks[0]:
        totalTime = totalTime + msg.time
        if msg.type == "set_tempo":  # Just in case there are other events in the tempo map
            if y == 0:
                x.append(tempoMapItem(totalTime, msg.tempo, msg.tempo))
                z.append(totalTime)
                # x.append([y, totalTime, msg.tempo, avgTempo])
                y = y + 1
            elif y == 1:
                avgTempo = x[y - 1].tempo
                x.append(tempoMapItem(totalTime, msg.tempo, avgTempo))
                z.append(totalTime)
                # x.append([y, totalTime, msg.tempo, avgTempo])
                y = y + 1
            else:
                avgTempo = rollingAverage(x[y - 1].time, totalTime, avgTempo, x[y - 1].tempo)
                x.append(tempoMapItem(totalTime, msg.tempo, avgTempo))
                z.append(totalTime)
                # x.append([y, totalTime, msg.tempo, avgTempo])
                y = y + 1

    return x, z


def readFourBytes(anim, start):
    x = []
    for y in range(4):  # Iterate through the 4 bytes that make up the starting number
        x.append(anim[start])
        start += 1
    xBytes = bytearray(x)
    x = int.from_bytes(xBytes, console.endian)
    return x, xBytes, start


def pullData(anim, start, animType):  # PP events seem to have 4 extra bytes in between events.
    # Always seems to be 0000. If not, gives warning.

    events, eventsByte, start = readFourBytes(anim, start)
    # print(start, events, eventsByte)
    eventsList = []
    # print(animType)
    for x in range(events):
        if animType == 'postproc':
            unknown, unknownByte, start = readFourBytes(anim, start)
            if unknown != 0:
                print("Unknown variable not equal to 0. Please contact script creator.")
        eventLen, eventLenByte, start = readFourBytes(anim, start)
        event = []
        for y in range(eventLen):
            event.append(chr(anim[start]))
            start += 1
        if event == []:
            event = eventsList[-1].event
        else:
            event = ''.join(event)
        time, timeByte, start = readFourBytes(anim, start)
        eventsList.append(venueItem(struct.unpack(console.pack, timeByte)[0] / 30, event))
        # print(eventsList[-1])
    # print("")
    return eventsList


def midiProcessing(mid):
    tempoMap, ticks = tempMap(mid)
    # for x in tempoMap:
    # print(x.time, x.tempo, x.avgTempo)
    """mid = mido.MidiFile(type=1)
    mid.add_track()  # "Tempo" track
    mid.tracks[0].append(mido.MetaMessage('set_tempo', tempo = 500000, time = 0))  # Create default mid of 120 BPM"""
    endEvent = 0
    for track in mid.tracks:
        if track.name == "EVENTS":
            for msg in track:
                endEvent += msg.time
                if msg.type == 'text':
                    if msg.text == '[end]':
                        break
    for x, y in enumerate(tempoMap):
        y.seconds = t2s(y.time, tpb, y.avgTempo)
    """tIter = iter(ticks)  # Generate an iterable of all the ticks where changes appear.
    tickList = []
    for x in range(endEvent):
        if x in ticks:
            curTick = next(tIter)
            curIndex = ticks.index(curTick)
        # print(x, returnSeconds(curTick, tempoMap[curIndex].avgTempo, x-curTick, tempoMap[curIndex].tempo))
        tickList.append(returnSeconds(curTick, tempoMap[curIndex].avgTempo, x - curTick, tempoMap[curIndex].tempo))
    print(endEvent == len(tickList))"""

    return tempoMap  # tickList


def take_closest(myList, myNumber):
    """
    Assumes myList is sorted. Returns closest value to myNumber.

    If two numbers are equally close, return the smallest number.
    """
    pos = bisect_left(myList, myNumber)
    if pos == 0:
        return myList[0]
    if pos == len(myList):
        return myList[-1]
    before = myList[pos - 1]
    after = myList[pos]
    if after - myNumber < myNumber - before:
        return after
    else:
        return before


def songArray(songMap):
    songTime = []
    songSeconds = []
    songTempo = []
    songAvgTempo = []
    for x, y in enumerate(songMap):
        songTime.append(y.time)
        songSeconds.append(y.seconds)
        songTempo.append(y.tempo)
        songAvgTempo.append(y.avgTempo)
    return songTime, songSeconds, songTempo, songAvgTempo


def parseMiloData(mid, container, merge=False):
    return

def defaultMidi():
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)
    track.append(MetaMessage('set_tempo', tempo = 500000, time = 0))
    track.append(MetaMessage('time_signature', numerator = 4, denominator = 4, time=0))
    return mid

def main(anim, mid, output):

    #startP = time.time()

    eventsDict = {}
    for x in animParts:
        start = anim.find(animParts[x]) + len(animParts[x])
        # The number of "interp" ending events is 5 bytes away from the title instead of the usual 13.
        if animParts[x].endswith(b'interp'):
            start += 5
        else:
            start += 13
        eventsDict[x] = pullData(anim, start, x)
    #for x in eventsDict['spot_vocal']:
        #print(x.time, x.event)
    songMap = midiProcessing(mid)
    songTime, songSeconds, songTempo, songAvgTempo = songArray(songMap)
    # print(songTime, songSeconds, songTempo, songAvgTempo)
    secondsArray = np.array(songSeconds)
    # print(secondsArray[secondsArray <= 0].max())

    toMerge = []
    for tracks in lights:
        timeStart = 0
        tempTrack = MidiTrack()
        prevType = 'note_off'
        for y, x in enumerate(eventsDict[tracks]):  # Goes through each event in the milo, and finds their time in ticks
            mapLower = secondsArray[secondsArray <= x.time].max()
            arrIndex = songSeconds.index(mapLower)
            timeFromChange = x.time - songSeconds[arrIndex]
            ticksFromChange = s2t(timeFromChange, tpb, songTempo[arrIndex])
            timeVal = songTime[arrIndex] + round(ticksFromChange) - timeStart
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
                    # print(tracks)
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
                        timeStart += tempTrack[-1].time
                        # timeStart += tempTrack[-1].time
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
                if tracks == 'lights':
                    textEvent = f'[lighting ({x.event})]'
                else:
                    textEvent = f'[{x.event}]'
                tempTrack.append(MetaMessage('text', text=textEvent, time=timeVal))
            timeStart += tempTrack[-1].time
            #if tracks == 'spot_vocal':
                #print(timeStart, x.event)
        toMerge.append(tempTrack)
    # for tracks in playerAnim:
    # for tracks in rest:
    mid.tracks.append(merge_tracks(toMerge))
    mid.tracks[-1].name = "lights"
    for tracks in separate:
        if tracks.startswith('shot_'):
            tname = 'venue_' + tracks[-2:]
        else:
            tname = tracks
        mid.add_track(name=tname)
        timeStart = 0
        for y, x in enumerate(eventsDict[tracks]):
            mapLower = secondsArray[secondsArray <= x.time].max()
            arrIndex = songSeconds.index(mapLower)
            timeFromChange = x.time - songSeconds[arrIndex]
            ticksFromChange = s2t(timeFromChange, tpb, songTempo[arrIndex])
            timeVal = songTime[arrIndex] + round(ticksFromChange) - timeStart
            if tracks == 'fog':
                textEvent = f'[Fog{x.event.capitalize()}]'
            else:
                textEvent = f'[{x.event}]'
            mid.tracks[-1].append(MetaMessage('text', text=textEvent, time=timeVal))
            #print(timeStart)
            timeStart += mid.tracks[-1][-1].time
    # print(mid.tracks[-1], len(eventsDict['shot_bg']))
    # for x in mid.tracks[-1]:
    # print(x)

    mid.save(filename=f'{output}_merged.mid')

    # print(songTicks[3840])
    # for key in eventsDict:
    """crowdIter = iter(eventsDict['crowd'])
    currIter = next(crowdIter)
    for x, y in enumerate(songTicks):
        if currIter.time <= y:
            print(x, y, currIter.event)
            try:
                currIter = next(crowdIter)
            except StopIteration:
                break
            except:
                print(f"Iteration failed.")

        pass  # print(mido.second2tick(event.time, tpb, 500000))"""

    # print(anim.find(animParts['postproc']) + len(animParts['postproc']))
    #endP = time.time()
    #print(f"Runtime of the program is {endP - startP}")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("No file found. Please run this script with a \".anim\" file and optionally a MIDI file to merge together")
        exit()
    extensions = {
    }
    for x in sys.argv:
        extensions[os.path.splitext(x)[1][1:]] = x
    try:
        with open(extensions['anim'], "rb") as f:
            anim = f.read()
    except KeyError:
        print("No anim file found.")
        exit()
    try:
        mid = MidiFile(extensions['mid'], clip=True)
    except:
        mid = defaultMidi()
    #print(extensions)
    #mid.print_tracks()
    output = os.path.splitext(sys.argv[1])[0]
    main(anim, mid, output)