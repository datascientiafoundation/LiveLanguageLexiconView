import os
import sys
import xml.sax
import PySimpleGUI as sg
import platform
if platform.uname()[0] == "Windows":
    # Windows only, to address blurry fonts
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
#elif platform.uname()[0] == "Linux":
#    name = "linux.so"
    

class SaxHandler(xml.sax.ContentHandler):
    def startDocument(self):
        pass

    def startElement(self, name, attrs):
        global langName, langCode, langDescription, langPublisher, langProv, lemmas, senses, synsets
        self.inDefinition = False
        if name == "Lexicon":
            langName = attrs.getValue("label")
            langCode = attrs.getValue("language")
            langDescription = attrs.getValue("dc:description")
            langPublisher = attrs.getValue("dc:publisher")
            langProv = attrs.getValue("dc:source").split("; ")
        elif name == "Lemma":
            self.currentLemma = attrs.getValue("writtenForm") 
            self.currentLemmaPos = attrs.getValue("partOfSpeech")
        elif name == "Sense":
            self.currentSense = attrs.getValue("id")
            word = {}
            word["senseId"] = self.currentSense
            word["synsetId"] = attrs.getValue("synset")
            word["pos"] = self.currentLemmaPos
            if self.currentLemma not in lemmas:
                lemmas[self.currentLemma] = []
            lemmas[self.currentLemma].append(word)
            sense = {}
            sense["word"] = self.currentLemma
            sense["pos"] = self.currentLemmaPos
            sense["synsetId"] = word["synsetId"]
            if word["senseId"] not in senses:
                senses[word["senseId"]] = sense
            else:
                senses[word["senseId"]]["word"] = sense["word"]
                senses[word["senseId"]]["pos"] = sense["pos"]
                senses[word["senseId"]]["synsetId"] = sense["synsetId"]
            if sense["synsetId"] not in synsets:
                synsets[sense["synsetId"]] = {}
                synsets[sense["synsetId"]]["lemmas"] = []
            synsets[sense["synsetId"]]["lemmas"].append(self.currentLemma)
        elif name == "Synset":
            synset = {}
            synset["ili"] = attrs.getValue("ili")
            synset["lexicalized"] = attrs.getValue("lexicalized")
            synsetId = attrs.getValue("id")
            self.currentSynset = synsetId
            synset["pos"] = attrs.getValue("partOfSpeech")
            if synsetId not in synsets:
                synsets[synsetId] = synset
            else:
                synsets[synsetId]["ili"] = synset["ili"]
                synsets[synsetId]["lexicalized"] = synset["lexicalized"]
                synsets[synsetId]["pos"] = synset["pos"]
        elif name == "Definition":
            synsets[self.currentSynset]["gloss"] = "[" + attrs.getValue("language") + "] "
            self.inDefinition = True
            # will add actuall gloss when we get to the PCDATA
        elif name == "SenseRelation":
            reltype = attrs.getValue("relType")
            target = attrs.getValue("target")
            if "relations" not in senses[self.currentSense]:
                senses[self.currentSense]["relations"] = {}
            if reltype not in senses[self.currentSense]["relations"]:
                senses[self.currentSense]["relations"][reltype] = []
            senses[self.currentSense]["relations"][reltype].append(target)
            # now add the inverse relation if applicable
            if reltype in inverseRelations:
                inverseSource = target
                inverseTarget = self.currentSense
                inverseReltype = inverseRelations[reltype]
                if inverseSource not in senses:
                    senses[inverseSource] = {}
                if "relations" not in senses[inverseSource]:
                    senses[inverseSource]["relations"] = {}
                if inverseReltype not in senses[inverseSource]["relations"]:
                    senses[inverseSource]["relations"][inverseReltype] = []
                senses[inverseSource]["relations"][inverseReltype].append(inverseTarget)
        elif name == "SynsetRelation":
            reltype = attrs.getValue("relType")
            target = attrs.getValue("target")
            if "relations" not in synsets[self.currentSynset]:
                synsets[self.currentSynset]["relations"] = {}
            if reltype not in synsets[self.currentSynset]["relations"]:
                synsets[self.currentSynset]["relations"][reltype] = []
            synsets[self.currentSynset]["relations"][reltype].append(target)
            # now add the inverse relation if applicable
            if reltype in inverseRelations:
                inverseSource = target
                inverseTarget = self.currentSynset
                inverseReltype = inverseRelations[reltype]
                if inverseSource not in synsets:
                    synsets[inverseSource] = {}
                if "relations" not in synsets[inverseSource]:
                    synsets[inverseSource]["relations"] = {}
                if inverseReltype not in synsets[inverseSource]["relations"]:
                    synsets[inverseSource]["relations"][inverseReltype] = []
                synsets[inverseSource]["relations"][inverseReltype].append(inverseTarget)

    def endElement(self, name):
        pass

    def characters(self, content):
        if self.inDefinition:
            synsets[self.currentSynset]["gloss"] = synsets[self.currentSynset]["gloss"] + content.strip()

def POS_DISPLAY(pos):
    return SText("(" + pos + ") ", font="Helvetica 12", text_color="red")

def GLOSS_DISPLAY(gloss):
    return SText(gloss, font="Helvetica 12")


def Collapsible(layout, key, title='', arrows=("–", "+"), collapsed=False):
    """
    User Defined Element
    A "collapsable section" element. Like a container element that can be collapsed and brought back
    :param layout:Tuple[List[sg.Element]]: The layout for the section
    :param key:Any: Key used to make this section visible / invisible
    :param title:str: Title to show next to arrow
    :param arrows:Tuple[str, str]: The strings to use to show the section is (Open, Closed).
    :param collapsed:bool: If True, then the section begins in a collapsed state
    :return:sg.Column: Column including the arrows, title and the layout that is pinned
    """
    global linkList
    linkList.append(key + "-BUTTON-")
    linkList.append(key + "-TITLE-")
    return sg.Column([[sg.T("          " + (arrows[1] if collapsed else arrows[0]), enable_events=True, k=key+'-BUTTON-', font="Helvetica 14 bold"),
                       sg.T(title, font="Helvetica 12 italic", enable_events=True, key=key+'-TITLE-')],
                      [sg.pin(sg.Column(layout, key=key, visible=not collapsed, metadata=arrows))]], pad=(0,0))

def SText(text, *positionalArgs, **keywordArgs):
    return sg.InputText(text, *positionalArgs, **keywordArgs, size=(len(text)+1, None), pad=0, use_readonly_for_disable=True, disabled=True, disabled_readonly_background_color="white", border_width=0)

def LText(text, k, *positionalArgs, **keywordArgs):
    global linkList
    linkList.append(k)
    return [sg.Text("►", key=k, enable_events = True, pad=0, border_width=0, font="Helvetica 12 bold", text_color="blue"), SText(text, *positionalArgs, **keywordArgs)]

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# ==================================================================================

WINDOW_TITLE = 'LiveLanguage Lexicon View'
posNames = {"n": "Noun", "v": "Verb", "a": "Adjective", "r": "Adverb"}
inverseRelations = {"hyponym": "hypernym", "hypernym": "hyponym", "mero_part": "holo_part", "holo_part": "mero_part", "mero_substance": "holo_substance", "holo_substance": "mero_substance", "mero_member": "holo_member", "holo_member": "mero_member", "subevent": "is_subevent_of", "is_subevent_of": "subevent", "attribute": "attribute", "metaphorically_related_concept": "metaphorically_related_concept", "metonymically_related_concept": "metonymically_related_concept", "is_aspect_of": "has_aspect", "has_aspect": "is_aspect_of", "metonym": "metonym", "cognate": "cognate", "derivation": "derivation", "antonym": "antonym", "also": "also", "similar": "similar"}
bias = (0, 0)
lemmas = {}
senses = {}
synsets = {}
relations = {}
langName = "undefined"
langCode = "undefined"
langPublisher = "undefined"
langDescription = "undefined"
langProv = []

# 
if len(sys.argv) < 1:
    print("An LMF/XML file is needed as input argument! Exiting.")
    sys.exit(1)
# 
    
# fn = sys.argv[1]

fn = open(resource_path("mon.xml"))
parser = xml.sax.make_parser()
handler = SaxHandler()
parser.setContentHandler(handler)
parser.parse(fn) # TODO: validation

sg.change_look_and_feel('LightGrey1') 

layoutTop = [
                [sg.Text(langName + ' LiveLanguage Lexicon [' + langCode + ']', font='Verdana 14 bold'), sg.Button("ℹ Info", key="infobutton")],
                [sg.Text('Word to search for:', font='Helvetica 12'), sg.InputText(key="wordinput", font='Helvetica 12',focus = True), sg.Button('Search Lexicon', bind_return_key = True)],
                [sg.Column([], key="content", size=(80,200))]
            ]
layoutBottom = [sg.Button('Quit')]


#section1 = [[sg.Input('Input sec 1', key='-IN1-')]]

layout = [ layoutTop,
           [sg.Text(key='-OUTPUT-', font='Helvetica 14 bold')],
           layoutBottom,
           #[Collapsible(section1, SEC1_KEY,  'Section 1', collapsed=True)]
         ]
            
window = sg.Window('LiveLanguage Lexicon View', layout, resizable = True)
# Event Loop to process "events" and get the "values" of the inputs
while True:
    linkList = []
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Quit': # if user closes window or clicks cancel
        break
    elif event == "infobutton":
        sg.popup_scrolled(langName + ' LiveLanguage Lexicon [' + langCode + ']', "", "Description: " + langDescription, "", "Publisher: " + langPublisher, "", "Data sources:\n" + " - " + "\n - ".join(langProv), title="Lexicon Info")
        continue
    elif event.startswith("LEMMA"):
        wordPostfix = event.split(":")[1]
        word = wordPostfix.split("_")[0] # remove postfix "_" and synset ID
    elif event.startswith("COLLAPSE_"):
        if event.endswith('-BUTTON-'):
            key = event[:-8]
        elif event.endswith('-TITLE-'):
            key = event[:-7]
        else:
            key = event
        window[key].update(visible=not window[key].visible)
        window[key + "-BUTTON-"].update("          " + (window[key].metadata[0] if window[key].visible else window[key].metadata[1]))
        contentSize = window["content"].get_size()
        newContentSize = (contentSize[0], contentSize[1] + 200)
        window["content"].set_size(newContentSize)
        continue
    else:
        word = values["wordinput"].strip()

    # TODO: escape dangerous characters
    word = word.replace('"', '')
    
    if word not in lemmas and not word == "":
        window["-OUTPUT-"].update('“' + word + '” not found!')
        continue
    contentByPos = {}
    window.set_cursor("watch")
    if word == "":
        pass
        #for synsetId in synsets:
        #    synset = synsets[synsetId]
        #    if "relations" not in synset or ("hypernym" not in synset["relations"] and synset["pos"] == "n"):
        #        pos = "n"
        #        relsByType = {}
        #        if "relations" in synset:
        #            synRelations = synset["relations"]
        #            for reltype in synRelations:
        #                for target in synRelations[reltype]:
        #                    targetSynset = synsets[target]
        #                    if reltype not in relsByType:
        #                        relsByType[reltype] = []
        #                    relsByType[reltype].append(targetSynset)
        #        if pos not in contentByPos:
        #            contentByPos[pos] = []
        #        content = {}
        #        if "gloss" not in synset:
        #            content["gloss"] = "???"
        #        else:
        #            content["gloss"] = synset["gloss"]
        #        content["relations"] = relsByType
        #        content["synsetId"] = synsetId
        #        content["lemmas"] = synset["lemmas"]
        #        contentByPos[pos].append(content)
        #print(len(contentByPos['n']))
    else:
        for wordAttrs in lemmas[word]:
            sense = senses[wordAttrs["senseId"]]
            pos = sense["pos"]
            relsByType = {}
            # find all sense relations
            if "relations" in sense:
                senseRelations = sense["relations"]
                for reltype in senseRelations:
                    for target in senseRelations[reltype]:
                        targetSense = senses[target]
                        if reltype not in relsByType:
                            relsByType[reltype] = []
                        relsByType[reltype].append(targetSense)
            synsetId = sense["synsetId"]
            if not synsetId:
                print(word + " not found.")
                sys.exit(0)
            synset = synsets[synsetId]
            if "relations" in synset:
                synRelations = synset["relations"]
                for reltype in synRelations:
                    for target in synRelations[reltype]:
                        targetSynset = synsets[target]
                        if reltype not in relsByType:
                            relsByType[reltype] = []
                        relsByType[reltype].append(targetSynset)
            if pos not in contentByPos:
                contentByPos[pos] = []
            content = {}
            content["gloss"] = synset["gloss"]
            content["relations"] = relsByType
            content["synsetId"] = synsetId
            content["lemmas"] = synsets[synsetId]["lemmas"]
            contentByPos[pos].append(content)
    layoutBody = []
    for pos in contentByPos:
        layoutBody.append([sg.Text(posNames[pos], font='Helvetica 12 bold')])
        for entry in contentByPos[pos]:
            layoutRow = []
            #layoutRow.append(POS_DISPLAY(pos))
            #for lemma in entry["lemmas"]:
            #    layoutRow = layoutRow + LText(lemma, "LEMMA:" + lemma + "_" + entry["synsetId"], enable_events = True, font='Helvetica 12 bold', text_color='blue')
            lemmaList = ", ".join(entry["lemmas"])
            layoutRow.append(SText(lemmaList, font="Helvetica 12 bold", text_color="blue"))
            layoutRow.append(GLOSS_DISPLAY("    " + entry["gloss"]))
            layoutBody.append(layoutRow)
            if entry["relations"]:
                for reltype in entry["relations"]:
                    collapsibleSection = []
                    for rel in entry["relations"][reltype]:
                        layoutRow = [sg.Text("              ", font="Helvetica 12 bold")]
                        #layoutRow.append(POS_DISPLAY(rel["pos"]))
                        #layoutRow = []
                        if "lemmas" in rel:
                            # it is a synset relation
                            lemmaList = rel["lemmas"]
                        else:
                            # it is a sense relation
                            lemmaList = [rel["word"]] # only one word for a sense relation!
                        for lemma in lemmaList:
                            lemmaKey = "LEMMA:" + lemma + "_" + entry["synsetId"]
                            layoutRow = layoutRow + LText(lemma, lemmaKey, enable_events = True, font='Helvetica 12 bold', text_color='blue')
                        if "gloss" in rel:
                            # it is a synset relation
                            gloss = rel["gloss"]
                        else:
                            # it is a sense relation
                            gloss = synsets[rel["synsetId"]]["gloss"]
                        layoutRow.append(GLOSS_DISPLAY(gloss))
                        collapsibleSection.append(layoutRow)
                    collapsibleSectionKey = "COLLAPSE_" + entry["synsetId"] + "_" + reltype
                    layoutBody.append([Collapsible(collapsibleSection, collapsibleSectionKey, title=" " + reltype + " relations", arrows=("–", "+"), collapsed = True)])
    layoutBody = [sg.Column(layoutBody, scrollable = True, key="content", expand_x = True, expand_y = True)] # size=window["content"].Size
    newLayout = [
                 [sg.Text(langName + ' LiveLanguage Lexicon [' + langCode + ']', font='Helvetica 14 bold'), sg.Button("ℹ Info", key="infobutton")],
                 [sg.Text('Word to search for:', font='Helvetica 12'), sg.InputText(key="wordinput", font='Helvetica 12', focus=True), sg.Button('Search Lexicon', bind_return_key = True)], 
                 [sg.Text(key='-OUTPUT-', font='Helvetica 14 bold')],
                 layoutBody,
                 [sg.Button('Quit')]
                ]
    currentLocation = window.CurrentLocation()
    adjustedLocation = (currentLocation[0] - bias[0], currentLocation[1] - bias[1])
    newWindow = sg.Window(WINDOW_TITLE, newLayout, location = adjustedLocation, resizable = True, finalize = True)
    newWindow.size = window.size
    newLocation = newWindow.CurrentLocation()
    if not newLocation == currentLocation:
        # window is migrating due to titlebar size: compensate it
        bias = (newLocation[0] - currentLocation[0], newLocation[1] - currentLocation[1])
    window.close()
    window = newWindow
    window["wordinput"].update(word)
    for linkKey in linkList:
        window[linkKey].set_cursor("hand2")
    window.set_cursor("arrow")
    window["-OUTPUT-"].update('“' + word + '”')

window.close()

