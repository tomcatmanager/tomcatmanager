#
# This is a .tape file for vhs, which will turn it into a gif
# run it like:
#
# $ vhs package.tape
#

Require "bpython"

Output package.gif

Set Framerate 15

Set FontFamily "MesloLGL Nerd Font Mono"
Set FontSize 14

Set Width 933
Set Margin 20
Set Padding 0

Set TypingSpeed 80ms

Type "bpython -q" Sleep 30ms Enter
Sleep .9s

Type "import tomcatmanager as tm" Sleep 200ms Enter
Sleep 1.4s

Type "tomcat = tm.TomcatManager(" Sleep 2.5s
Type ")" Sleep 180ms Enter
Sleep 1s

Type@60ms 'r = tomcat.connect(url="http://localhost:8080/manager", user="ace", password="newenglandclamchowder")' Sleep 190ms Enter
Sleep 1.8s

Type 'tomcat.is_connected' Sleep 160ms Enter
Sleep 2s

Type 'r = tomcat.stop("/someapp")' Sleep 190ms Enter
Sleep 2s

Type 'r.status_code == tm.StatusCode.OK' Sleep 200ms Enter
Sleep 2s

Type 'r.status_message' Sleep 180ms Enter
Sleep 2.5s

Type "exit()" Sleep 150ms Enter
Sleep 1.5s
