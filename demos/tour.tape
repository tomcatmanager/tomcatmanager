#
# This is a .tape file for vhs, which will turn it into a gif
# run it like:
#
# $ vhs tour.tape
#

Output tour.gif

Set Framerate 15

Set FontFamily "MesloLGL Nerd Font Mono"
Set FontSize 14

Set Width 933
Set Margin 20
Set Padding 0

Set TypingSpeed 60ms

Type "tomcat-manager" Sleep 30ms Enter
Sleep 1.1s
Type@40ms "connect http://localhost:8080/manager ace" Sleep 200ms Enter
Type@40ms "newenglandclamchowder" Enter
Sleep 2s

Type "list" Sleep 200ms Enter
Sleep 2s

Type "deploy local tests/war/sample.war /sampleapp" Sleep 190ms Enter
Sleep 1.75s

Type "list" Sleep 350ms Enter
Sleep 1.75s

Type "help" Sleep 150ms Enter
Sleep 3s
Space
Sleep 3s
Space
Sleep 3s
Type "q"
Sleep 2s

Type "help undeploy" Sleep 250ms Enter
Sleep 3s

Type "undeploy /sampleapp" Sleep 325ms Enter
Sleep 2.5s

Type "list" Sleep 275ms Enter
Sleep 2.25s

Type "set" Sleep 300ms Enter
Sleep 3s

Type "theme list" Sleep 350ms Enter
Sleep 3s

Type "exit" Enter
Sleep 1.5s
