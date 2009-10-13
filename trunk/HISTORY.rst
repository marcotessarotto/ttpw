2009-10-13
Initial import of project on SourceSup subversion hosting.
Moved history from module docstring into this file.

2009-09-28
Modified TagText like Katie Bell indicate when the tagonly options is used
(consider the input text to ba already pre-processed, and to only be a set
of lines with one TreeTagger token per line) (bug signaled by Joel Nothman
too).
Added support for spanish using Marco Turchi proposed 'es' options in
g_langsupport.
Fixed bug in StartProcess when creating tagcmd string (quote the tagparfile
parameter).

2007-12-19
Switch to unicode internally, encode / decode outputs and inputs.

2007-12-19
Integration of patch from Frédéric Fauberteau to resolve the translate problem,
and to fix -d option misstyping in getopt.

2005-09-29
Added support for darwin on the request of (and with tests from)
Mauro Cherubini.
