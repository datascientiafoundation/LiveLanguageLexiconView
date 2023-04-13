# LiveLanguage Lexicon Viewer

A simple, multi-platform tool for viewing the contents of monolingual lexicons.

On Windows, you can run the EXE file directly, but you have to provide it with an input lexicon as argument. For example, the example Quechua lexicon included in the distribution can be loaded as follows:

```console
C:\my\path\> llview.exe que.xml
```

If you wish to build the tool directly from the Python source (which is what you have to do under Linux), you will need Python 3 and PySimpleGui installed.

```console
$ pip install pysimplegui
```

Then the tool is run as follows (loading the Quechua lexicon):

```console
$ python3 llview.py que.xml
```
